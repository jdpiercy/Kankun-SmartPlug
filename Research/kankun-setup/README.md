# kankun-setup
CLI setup script for kankun wifi plugs

Connects through SSH to the plug, configures it to be on the wifi network specified, copies any files in the `setup` folder, restarts the plug and then runs the `install.sh` file.

## Setup
1. You need Node and npm installed
2. Clone this repo
3. Run `npm install` inside the repo

## How to use
1. Add any files you want copied to the plug into the `setup` folder.
2. Edit `setup/install.sh` with any commands you want to run on the first reboot.
3. Connect to the Kankun plug's wifi access point. This should be `0K_SP3`
4. Run the script using `node index.js` and answer the prompts or using `node index.js --ssid=<<network ssid>> --key=<<network key>>` to skip the prompts
