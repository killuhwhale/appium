#!/user/bin/bash

sudo apt install default-jre

if [ -e "/opt/android-studio" ]
then
    # The file exists
    echo "Android studio already installed."
else
    echo "Fetching Android Studio"

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

    echo "Downloading from: $STUDIO..."
    echo "Downloading Android Studio for Chrome."
    curl -o studio.deb -L $STUDIO

    echo "Installing Android Studio for Chrome."

    sudo dpkg -i  studio.deb

    echo "Done downloading and installing Android Studio"

    sudo rm studio.deb

    echo "Search for app: Android Studio"

    bash /opt/android-studio/bin/studio.sh

fi


