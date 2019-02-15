#!/usr/bin/python
import cgi
import sys
import SocketServer
import BaseHTTPServer
from itertools import cycle, islice, chain
from StringIO import StringIO
from string import Template
import datetime
import time
import json
import calendar
from urllib2 import urlopen, Request
from collections import namedtuple

from flask import Flask, request, render_template
app = Flask(__name__)

class State:
    off, on = range(2)
    def __init__(self, val):
        if isinstance(val, unicode) or isinstance(val, str):
            self._val = {u'OFF': self.off , u'ON': self.on}[val]
        else:
            self._val = val
    @property
    def name(self):
        return [u'OFF', u'ON'][self._val]
    
    @property
    def value(self):
        return self._val
    
    def __invert__(self):
        if self._val == self.off:
            return State(self.on)
        return State(self.off)
    
    def __repr__(self):
        return "%s:(%d/%s)" % (self.__class__.__name__, self._val, self.name)

VALID_DAYS = list(calendar.day_abbr)

class SunTimeDiff(object):
    def __init__(self, config_str):
        x = config_str.split()
        assert len(x) == 3 and x[0].lower() in ['$sunset', '$sunrise'] \
            and x[1] in ['+', '-']

        self.sunstate = x[0].lower()
        op = x[1]
        mins = x[2]
        self.timediff = datetime.timedelta(minutes=int(op + mins))

__suntimes_cache = {}
def get_suntimes(day):
    global __suntimes_cache
    if day in __suntimes_cache:
        return __suntimes_cache[day]

    location_dict = __config["location"]

    tm = time.localtime()
    date_str = '%d-%02d-%02d' % (day.year, day.month, day.day)
    url = 'http://api.sunrise-sunset.org/json?lat=%s&lng=%s&date=%s' % \
        (location_dict["lat"], location_dict["long"], date_str)
    request = Request(url)
    response = urlopen(request)
    time_dict = json.loads(response.read())
    if time_dict["status"] != "OK":
        return None
    times = {}
    for x in ["sunset", "sunrise"]:
        utc_time = time.strptime(date_str + " " + time_dict["results"][x], "%Y-%m-%d %I:%M:%S %p")
        times["$" + x] = calendar.timegm(utc_time)
    __suntimes_cache[day] = times
    return times

TransitionInfo = namedtuple('TransitionInfo', ['datetime', 'state'])

class TimerConfig:
    MODE_AUTO = 0
    MODE_MANUAL_ON = 1
    MODE_MANUAL_OFF = 2
    MODE_COUNT = 3

    def __init__(self, nickname, schedule = None):
        self.schedule = schedule
        self.nickname = nickname
        self.mode = TimerConfig.MODE_AUTO
    
    def do_button(self):
        self.mode = (self.mode + 1) % TimerConfig.MODE_COUNT
    
    def set_mode(self, mode):
        self.mode = {"ON": TimerConfig.MODE_MANUAL_ON,
                     "OFF": TimerConfig.MODE_MANUAL_OFF,
                     "AUTO": TimerConfig.MODE_AUTO}[mode.upper()]
    def get_mode(self):
        if self.mode == TimerConfig.MODE_AUTO:
            return "AUTO"
        return "MANUAL"
    
    def get_powered(self):
        if self.mode == TimerConfig.MODE_AUTO:
            time, current_state = self.get_transitions_from_current().next()
            return current_state.name
        else:
            return {TimerConfig.MODE_MANUAL_OFF:"OFF", TimerConfig.MODE_MANUAL_ON:"ON"}[self.mode]

    def get_radioselect_text(self, mode):
        modes = {'on': TimerConfig.MODE_MANUAL_ON, 'off': TimerConfig.MODE_MANUAL_OFF, 'auto':TimerConfig.MODE_AUTO}
        for k, v in modes.iteritems():
            if mode == k and self.mode == v:
                return "checked"
        return ""

    def get_transition_list(self):
        """
            Returns a generator of tuples in the form:
            ( datetime.datetime object, ON/OFF)
        """
        def get_item_key(obj_list):
            key = obj_list.datetime
            if (isinstance(key, SunTimeDiff)):
                suntimes = get_suntimes(start_day)
                dt = datetime.datetime.fromtimestamp(suntimes[key.sunstate]) + key.timediff
                return "%02d%02d" % (dt.hour, dt.minute)
            return key

        timediff = datetime.timedelta(days=1)
        start_day = datetime.date.today()
        # This first needs to find the first day >= "today" that exists in the schedule
        for d in list(islice(cycle(calendar.day_abbr), start_day.weekday(), start_day.weekday() + 7)):
            if d in self.schedule and len(self.schedule[d]) > 0:
                dt = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
                first = sorted(self.schedule[d], key=get_item_key)[0]
                yield TransitionInfo(dt, ~first[1])
                break
            start_day += timediff
        while True:
            d = calendar.day_abbr[start_day.weekday()]
            if d in self.schedule:
                for t,s in sorted(self.schedule[d], key=get_item_key):
                    real_time = get_item_key(TransitionInfo(t, State("ON"))) # fixme, put the datetime obj instead of the string
                    hr = int(real_time[0:2], base=10)
                    mins = int(real_time[2:], base=10)
                    yield TransitionInfo(datetime.datetime.combine(start_day, datetime.time(hr, mins)), s)
            start_day += timediff
    
    def get_transitions_from_current(self):
        """Returns a generator with the first being the current state"""
        if self.mode != TimerConfig.MODE_AUTO:
            return None
        transitions = self.get_transition_list()
        idx = 0
        now = datetime.datetime.now()
        while now > transitions.next()[0]:
            idx += 1
        return islice(self.get_transition_list(), idx - 1, None)
            
    def get_next_transitions(self, amount=2):
        return list(islice(self.get_transitions_from_current(), 1, 1 + amount))
        
    def get_next_change_text(self):
        if self.mode != TimerConfig.MODE_AUTO:
            return "Timer is forced to %s, change setting below" % (self.get_powered())
        time, s = self.get_next_transitions()[0]
        state = s.name
        hr = time.hour
        mins = time.minute
        d = calendar.day_abbr[time.weekday()]
        if time.weekday() != datetime.date.today().weekday():
            day_suffix = " on %s" % (d)
        else:
            day_suffix = ""
        return "Timer will turn %s at %s:%s%s" % (state, hr, mins, day_suffix)

def load_from_dict(cfg):
    def load_schedule_array(schedule):
        for k, v in schedule.iteritems():
            state = State(v)
            if k.split()[0] in ['$sunset', '$sunrise']:
                yield TransitionInfo(SunTimeDiff(k), state)
            else:
                yield TransitionInfo(k, state)
    timers = {}
    for x in cfg["timers"]:
        addr = x["addr"]
        nick = x["nickname"]
        schedule = {}
        for day, items in x["schedule"].iteritems():
            if day not in VALID_DAYS:
                continue
            schedule[day] = []
            for j in items:
                schedule[day] += list(load_schedule_array(j))
        timers[addr] = TimerConfig(nick, schedule)

    return {"timers": timers, "location": cfg["location"]}

__config = None

@app.route('/api/0.1/<timer_addr>')
def handle_get_state(timer_addr):
    if timer_addr not in __config["timers"]:
        return None
    config = __config["timers"][timer_addr]
    
    power_str = config.get_powered()
    mode_str = config.get_mode()
    
    return "power=%s timer=%s" % (power_str, mode_str)

@app.route('/api/0.1/<timer_addr>/button')
def handle_do_button(timer_addr):
    if timer_addr not in __config["timers"]:
        return None
    config = __config["timers"][timer_addr]
    config.do_button()
    return handle_get_state(timer_addr)

def get_next_change_text(timer_addr):
    if timer_addr not in __config["timers"]:
        return ""
    time, s = __config["timers"][timer_addr].get_next_transitions()[0]
    state = s.name
    hr = time.hour
    mins = time.minute
    d = calendar.day_abbr[time.weekday()]
    if time.weekday() != datetime.date.today().weekday():
        day_suffix = " on %s" % (d)
    else:
        day_suffix = ""
    return "Timer will turn %s at %s:%s%s" % (state, hr, mins, day_suffix)
    

def get_config(name):
    if name in __config["timers"].keys():
        return __config["timers"][name]
    return None
    
def find_config_from_nick(name):
    for k,v in __config["timers"].iteritems():
        if v.nickname.lower() == name.lower():
            return (v,k)
    return (None, None)

@app.route('/<addr>', methods=['GET', 'POST'])
def get_one_html(addr):
    cfg = get_config(addr)
    if not cfg:
        cfg, addr = find_config_from_nick(addr)
    if not cfg:
        return None
    if request.method == 'POST':
        cfg.set_mode(request.form.get('force'))

    return render_template('index.html', timers={addr: cfg})

@app.route('/', methods=['GET', 'POST'])
def get_html():
    if request.method == 'POST':
        addr = request.form.get('addr')
        cfg = get_config(addr)
        if not cfg:
            cfg, addr = find_config_from_nick(addr)
        if not cfg:
            return None
        cfg.set_mode(request.form.get('force'))

    return render_template('index.html', timers=__config["timers"])

if __name__ == "__main__":
    with open('config.json', 'r') as fh:
        jscfg = json.load(fh)
        __config = load_from_dict(jscfg)
    if len(sys.argv) > 1:
        app.run(debug=True)
    else:
        app.run(host='0.0.0.0', port=8100)
