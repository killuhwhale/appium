# echo "password" | sudo -S myscript.sh
# Install Java
Red="\033[31m"
Black="\033[30m"
Green="\033[32m"
Yellow="\033[33m"
Blue="\033[34m"
Purple="\033[35m"
Cyan="\033[36m"
White="\033[37m"
RESET="\033[0m"


sudo apt -y install default-jre
sudo apt -y install libnss3-dev libgdk-pixbuf2.0-dev libgtk-3-dev libxss-dev

# Setup Node environment

num_files=$(ls -1a $NVM_DIR | wc -l)
key_len=${#NVM_DIR}
echo -e "\n\n $Green Checking NODE ENV: ($num_files) - ($key_len) $RESET \n\n"


if [ $num_files -gt 0 -a $key_len -gt 0 ]; then
  # If nvm is installed, print "Installed"
  echo -e "\n\n $Blue Node Installed $RESET \n\n"
else
    # If nvm is not installed, print "Not installed"
    echo -e "\n\n $Red Node Not Installed $RESET \n\n"
    echo -e "\n\n $Yellow Installing node... $RESET \n\n"
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash

    echo -e "\n\n $Blue Installed NVM $RESET \n\n"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm

    echo "If nvm or npm not command seen, run "
    echo -e "\n\n $Cyan If nvm or npm not command seen, Run: \n\t $Red exec bash $RESET \n $Cyan and rerun script! $RESET \n\n"

    source ~/.bashrc
    echo -e "\n\n $Blue Installing Node 18.7.0 $RESET \n\n"
    nvm install 18.7.0
    nvm use node
    echo -e "\n\n $Yellow Installing npm appium... $RESET \n\n"
    npm install -g appium
fi




bash append_to_bashrc.sh "export ANDROID_HOME=/home/\$USER/Android/Sdk" "/home/$USER/.bashrc"
bash append_to_bashrc.sh "export PATH=\$PATH:\$ANDROID_HOME/platform-tools:\$ANDROID_HOME/tools:\$ANDROID_HOME/build-tools;" "/home/$USER/.bashrc"
bash append_to_bashrc.sh "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" "/home/$USER/.bashrc"
bash append_to_bashrc.sh "export PATH=\$PATH:\$JAVA_HOME" "/home/$USER/.bashrc"




if [ ! -e "/home/$USER/appium" ]; then
    echo -e "\n\n $Green Cloning repo & setting up env... $RESET \n\n"
    sudo apt-get install python3-venv
    git clone https://github.com/killuhwhale/appium.git
    cd appium
    python3 -m venv .
    source bin/activate
    cd src
    pip install -r requirements.txt
else
    echo -e "\n\n $Yellow Source env already setup... $RESET \n\n"
    cd appium/src
fi
echo -e "\n\n $Cyan Finished! Run: \n\t $RESET $Red exec bash $RESET \n\n"

echo -e "\n\n $Cyan Also don't forget to activate venv:: \n\t $RESET $Red source appium/bin/activate $RESET \n\n"

echo -e "\n\n $Cyan To run: cd appium/src \n\t $RESET $Red python3 main.py 192.168.0.123:5555 192.168.0.235:5555 $RESET \n\n"