# echo "password" | sudo -S myscript.sh
# Install Java
sudo apt install default-jre
sudo apt install libnss3-dev libgdk-pixbuf2.0-dev libgtk-3-dev libxss-dev

# Setup Node environment

num_files=$(ls -1a $NVM_DIR | wc -l)
if [ $num_files -gt 0 ]; then
  # If nvm is installed, print "Installed"
  echo "Installed"
else
    # If nvm is not installed, print "Not installed"
    echo "Not installed"
    touch ~/.bashrc
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash

    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm

    nvm install 18.7.0
    nvm use node
    npm install -g appium
fi


bash ins_and_stu.sh

bash append_to_bashrc.sh "export ANDROID_HOME=/home/\$USER/Android/Sdk" "/home/$USER/.bashrc"
bash append_to_bashrc.sh "export PATH=\$PATH:\$ANDROID_HOME/platform-tools:\$ANDROID_HOME/tools:\$ANDROID_HOME/build-tools;" "/home/$USER/.bashrc"
bash append_to_bashrc.sh "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64" "/home/$USER/.bashrc"
bash append_to_bashrc.sh "export PATH=\$PATH:\$JAVA_HOME"




if [ ! -e "/home/$USER/appium" ]; then
    sudo apt-get install python3-venv
    git clone https://github.com/killuhwhale/appium.git
    cd appium
    python3 -m venv .
    source bin/activate
    cd src
    pip install -r requirements.txt
else
    cd appium/src
fi


python3 main.py