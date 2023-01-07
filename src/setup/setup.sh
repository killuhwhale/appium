# echo "password" | sudo -S myscript.sh
# Install Java
sudo apt install default-jre
apt install libnss3-dev libgdk-pixbuf2.0-dev libgtk-3-dev libxss-dev

# Setup Node environment
touch ~/.bashrc
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash
source ~/.bashrc
nvm install 18.7.0
nvm use node
npm install -g appium

bash ins_and_stu.sh



bash append_to_bashrc.sh "export ANDROID_HOME=/home/$USER/Android/Sdk"
bash append_to_bashrc.sh "export PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/tools:$ANDROID_HOME/build-tools;"
bash append_to_bashrc.sh "export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64"
bash append_to_bashrc.sh "export PATH=$PATH:$JAVA_HOME"






sudo apt-get install python3-venv
git clone https://github.com/killuhwhale/appium.git
cd appium
python3 -m venv .
source bin/activate
cd src
pip install -r requirements.txt
