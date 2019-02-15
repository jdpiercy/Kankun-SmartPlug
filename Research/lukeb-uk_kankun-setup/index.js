var bluebird = require('bluebird'),
    Client = require('ssh2').Client,
    telnet = require('telnet-client'),
    Hapi = require('hapi'),
    Inert = require('inert'),
    argv = require('yargs').argv,
    prompt = bluebird.promisifyAll(require('prompt')),
    fs = bluebird.promisifyAll(require('fs')),
    ip = require('ip'),
    passwords = ['p9z34c', 'admin', '1234'],
    sshConnect,
    telnetConnect,
    server,
    key,
    ssid;

sshConnect = function(password) {
    var conn = bluebird.promisifyAll(new Client());
    conn.on('ready', function() {
        conn.execAsync('mkdir /setup').then(function(stream) {
            return new bluebird(function(resolve, reject) {
                stream.on('close', function(code, signal) {
                    console.log('Setup directory created on plug');
                    resolve(conn.execAsync('wget -O /etc/hotplug.d/iface/40-setup "http://' + ip.address() + ':3000/setup.sh"'));
                });
            });
        }).then(function(stream) {
            return new bluebird(function(resolve, reject) {
                stream.on('close', function(code, signal) {
                    console.log('Copied setup.sh');
                    resolve(fs.readdirAsync('./setup'));
                });
            });
        }).then(function copyFiles(path, files) {
            if (typeof path !== 'string') {
                files = path;
                path = ''
            }
            return bluebird.map(files, function(file) {
                return fs.statAsync('./setup' + path + '/' + file).then(function(stats) {
                    if (stats.isDirectory()) {
                        return conn.execAsync('mkdir /setup'+ path + '/' + file).then(function(stream) {
                            return new bluebird(function(resolve, reject) {
                                stream.on('close', function(code, signal) {
                                    resolve(
                                        fs.readdirAsync('./setup' + path + '/' + file )
                                            .then(copyFiles.bind(this, path + '/' + file))
                                    );
                                });
                            });
                        });
                    } else {
                        return conn.execAsync('cd /setup' + path + '; wget -O ' + file + ' "http://' + ip.address() + ':3000/setup' + path + '/' + file + '"')
                            .then(function(stream) {
                                return new bluebird(function(resolve, reject) {
                                    stream.on('close', function(code, signal) {
                                        console.log('Copied ' + path + '/' + file);
                                        resolve();
                                    });
                                });
                            });
                    }
                })

            });
        }).then(function() {
            return conn.execAsync('cat /etc/config/wireless').then(function(stream) {
                return new bluebird(function(resolve, reject) {
                    var config = '';
                    stream.on('data', function(data) {
                        config += data.toString();
                    });

                    stream.on('close', function(code, signal) {
                        var configParts = config.split('\n\n');

                        bluebird.map(configParts, function(value, i) {
                            if (value.match('config wifi-iface')) {
                                return 'config wifi-iface\n\t' +
                                    'option device \'radio0\'\n\t' +
                                    'option network \'wwan\'\n\t' +
                                    'option ssid \'' + ssid + '\'\n\t' +
                                    'option mode \'sta\'\n\t' +
                                    'option encryption \'psk2\'\n\t' +
                                    'option key \'' + key + '\'';
                            }
                            return value;
                        }).then(function(parts) {
                            config = parts.join('\n\n');

                            resolve(config);
                        });
                    });
                });
            });
        }).then(function(config) {
            return conn.execAsync('echo -e "' + config + '" > /etc/config/wireless');
        }).then(function(stream) {
            return new bluebird(function(resolve, reject) {
                stream.on('close', function(code, signal) {
                    resolve(conn.execAsync('echo -e "\nconfig interface \'wwan\'\n\toption proto dhcp\n" >> /etc/config/network'));
                });
            });
        }).then(function(stream) {
            return new bluebird(function(resolve, reject) {
                stream.on('close', function(code, signal) {
                    console.log('Updated Wireless Config');
                    console.log('Rebooting')
                    resolve(conn.execAsync('reboot'));
                });
            });
        }).then(function(stream) {
            return new bluebird(function(resolve, reject) {
                stream.on('close', function(code, signal) {
                    conn.end();
                    server.stop();
                });
            });
        });
    }).on('error', function(err) {
        var passwordIndex = passwords.indexOf(password);
        if (err.level === 'client-authentication' && passwordIndex < (passwords.length -1)) {
            sshConnect(passwords[(passwordIndex + 1)]);
        } else {
            telnetConnect();
        }
    }).connect({
        host: '192.168.10.253',
        username: 'root',
        password: password
    });
};

telnetConnect = function() {
    var connection = new telnet(),
        params = {
            host: '192.168.10.253'
        };

    connection.connect(params).then(function(prompt) {
        connection.exec('echo -e "' + passwords[0] + '\n' + passwords[0] + '" | passwd')
            .then(function(res) {
                console.log('SSH Password was unset, now set to ' + passwords[0]);
                connection.end();
                sshConnect(passwords[0]);
            })
    });
};

server = new Hapi.Server({
    connections: {
        routes: {
            files: {
                relativeTo: __dirname
            }
        }
    }
});

server.connection({ port: 3000 });

server.register(Inert, () => {});

server.route({
    method: 'GET',
    path: '/{param*}',
    handler: {
        directory: {
            path: '.',
            redirectToSlash: true,
            index: true
        }
    }
});

server.start((err) => {
    if (err) {
        throw err;
    }
});

prompt.override = argv;
prompt.message = '';
prompt.delimiter = '';
prompt.colors = false;
prompt.start();

prompt.getAsync([{
    name: 'ssid',
    description: 'Network SSID: '
}, {
    name: 'key',
    description: 'Network Key: '
}]).then((result) => {
    ssid = result.ssid;
    key = result.key;
    sshConnect(passwords[0]);
});
