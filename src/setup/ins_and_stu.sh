#!/user/bin/bash

sudo apt -y install default-jre

RED="\033[31m"
Black="\033[30m"
Green="\033[32m"
Yellow="\033[33m"
Blue="\033[34m"
Purple="\033[35m"
Cyan="\033[36m"
White="\033[37m"
RESET="\033[0m"



if [ -e "/opt/android-studio" ]
then
    # The file exists
    echo -e "\n\n $Green Android studio already installed. $RESET \n\n"
else
    echo -e "\n\n $Green Fetching Android Studio. $RESET \n\n"

    # Link from studio website
    # curl https://redirector.gvt1.com/edgedl/android
    #   /studio/install/2021.2.1.15/android-studio-2021.2.1.15-cros.deb
    AS_DL_URL=$(curl "https://developer.android.com/studio/index.html#downloads" | grep -o -m 1 --regexp='https.*\.deb')
    echo "Found DL Link: $AS_DL_URL"

    # Regex Extract
    # The document has moved
    # <A HREF="https://r3---sn-o097znss.gvt1.com/edgedl/android/studio
    #   /install/2021.2.1.15/android-studio-2021.2.1.15-cros.deb?cms_redirect=yes&amp;mh=D\
    #   -&amp;mip=192.145.118.165&amp;mm=28&amp;mn=sn-o097znss&amp;ms=nvh&amp;mt=1654888163&amp;mv=u&amp;mvi=3&amp;pl=24&amp;shardbypass=sd&amp;smhost=r5---\
    #    sn-o097znze.gvt1.com">here</A>.

    # STUDIO=$(curl https://redirector.gvt1.com/edgedl/android
    #   /studio/install/2021.2.1.15/android-studio-2021.2.1.15-cros.deb
    #    | grep -o --regexp='https.\*com')
    STUDIO=$(curl $AS_DL_URL | grep -o --regexp='https.*com')

    echo -e "\n\n $Purple Downloading from: $STUDIO... $RESET \n\n"
    echo -e "\n\n $Purple Downloading Android Studio for Chrome. $RESET \n\n"
    curl -o studio.deb -L $STUDIO

    echo -e "\n\n $Yellow Installing Android Studio for Chrome.. $RESET \n\n"
    sudo dpkg -i  studio.deb

    sudo rm studio.deb

    echo -e "\n\n $Green Opening Android Studio. $RESET \n\n"

    bash /opt/android-studio/bin/studio.sh

fi


