import re
import subprocess
from enum import Enum
from time import time
from typing import AnyStr, Dict, List


# ARC_VERSIONS
class ARC_VERSIONS(Enum):
    ARC_P = 1
    ARC_R = 2

def get_cur_activty(transport_id: str, ARC_VERSION: ARC_VERSIONS = ARC_VERSIONS.ARC_R) -> List[str]:

    MAX_WAIT_FOR_OPEN_APP = 420  # 7 mins
    t = time()
    while int(time() - t) < MAX_WAIT_FOR_OPEN_APP:
        try:
            '''
            
                ARC-P
                mResumedActivity: ActivityRecord{9588d06 u0 com.netflix.mediaclient/o.cwK t127}
                ARC-R
                mFocusedWindow=Window{b3ef1fc u0 NotificationShade} ## Sleep
                mFocusedWindow=Window{3f50b2f u0 com.netflix.mediaclient/com.netflix.mediaclient.acquisition.screens.signupContainer.SignupNativeActivity}
            '''
            keyword = ""
            if ARC_VERSION == ARC_VERSIONS.ARC_P:
                keyword = "mResumedActivity"
            if ARC_VERSION == ARC_VERSIONS.ARC_R:
                keyword = "mFocusedWindow"
            print("Key word ", ARC_VERSIONS.ARC_R, ARC_VERSION,  keyword)
            cmd = ('adb', '-t', transport_id, 'shell', 'dumpsys', 'activity', 
                    '|', 'grep', keyword)
            text = subprocess.run(cmd, encoding='utf-8',
                capture_output=True).stdout.strip()
            print("res text: ", text)

            query = r".*{.*\s.*\s(?P<package_name>.*)/(?P<act_name>[\S\.]*)\s*.*}"
            result = re.search(query, text)
            
            if result is None:
                print("Cant find current activity.")
                return "",""
            
            print(result.group("package_name"), result.group("act_name"))
            return result.group("package_name"), result.group("act_name")
        except Exception as e:
            print("Err get_cur_activty ", e)
    return "",""
    
def open_app(package_name: str, transport_id: int, ARC_VERSION: ARC_VERSIONS = ARC_VERSIONS.ARC_R):
    try:
        cmd = ('adb','-t', transport_id, 'shell', 'monkey', '--pct-syskeys', '0', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1')
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print(f"Starting {package_name} w/ monkey...")

        # Call get activty and wait until the package name matches....
        cur_package = ""
        MAX_WAIT_FOR_OPEN_APP = 420  # 7 mins
        t = time()
        while cur_package != package_name and int(time() - t) < MAX_WAIT_FOR_OPEN_APP:
            try:
                cur_package, act_name = get_cur_activty(transport_id, ARC_VERSION)
            except Exception as e:
                print("Err getting cur act", e)
        print(outstr)


    except Exception as e:
        print("Error opening app with monkey", e)
        return False
    return True

def close_app(package_name: str, transport_id: int):
    try:
        cmd = ('adb', '-t', transport_id, 'shell', 'am', 'force-stop', package_name)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print(f"Closed {package_name}...")
        print(outstr)
    except Exception as e:
        print("Error closing app with monkey", e)
        return False
    return True


def adb_connect(ip: str):
    try:
        cmd = ('adb', 'connect', ip)
        outstr = subprocess.run(cmd, check=True, encoding='utf-8',
                                capture_output=True).stdout.strip()
        print(outstr)
    except Exception as e:
        print("Error connecting to ADB", e)
        return False
    return True

def android_des_caps(device_name: AnyStr, app_package: AnyStr, main_activity: AnyStr) -> Dict:
    return {
        'platformName': 'Android',
        'appium:udid': device_name,
        'appium:appPackage': app_package,
        'appium:automationName': 'UiAutomator2',
        'appium:appActivity': main_activity,
        'appium:ensureWebviewHavepages': "true",
        'appium:nativeWebScreenshot': "true",
        'appium:newCommandTimeout': 3600,
        'appium:connectHardwareKeyboard': "true",
        'appium:noReset': True,
        "appium:uiautomator2ServerInstallTimeout": 60000
    }


def find_transport_id(ip_address)-> str:
  # Call the adb command to list devices
  cmd = ('adb', 'devices', '-l')
  outstr = subprocess.run(cmd, check=True, encoding='utf-8', capture_output=True).stdout.strip()
  print(outstr)
  # Split the output into a list of lines
  lines = outstr.split("\n")
  # Iterate over the lines
  for line in lines:
    # Split the line into words
    words = line.split()
    # Check if the IP address is in the line
    print("Checking ", ip_address, "  ", words)
    if ip_address in words:
      # The transport ID is the first word in the line
      return words[-1].split(":")[-1]
  # If the IP address was not found, return None
  return '-1'


def get_arc_version(transport_id: str):
    cmd = ('adb','-t', transport_id, 'shell', 'getprop', "ro.build.version.release")
    try:
        res = subprocess.run(cmd,  encoding='utf-8', capture_output=True).stdout.strip()
        print("Res: ", res)
        if res == "9":
            return ARC_VERSIONS.ARC_P
        elif res == "11":
            return ARC_VERSIONS.ARC_R
    except:
        print("Cannot find Android Version")    
    return None

EXECUTOR = 'http://192.168.0.175:4723/wd/hub'

ADB_KEYCODE_UNKNOWN = "0"
ADB_KEYCODE_MENU = "1"
ADB_KEYCODE_SOFT_RIGHT = "2"
ADB_KEYCODE_HOME = "3"
ADB_KEYCODE_BACK = "4"
ADB_KEYCODE_CALL = "5"
ADB_KEYCODE_ENDCALL = "6"
ADB_KEYCODE_0 = "7"
ADB_KEYCODE_1 = "8"
ADB_KEYCODE_2 = "9"
ADB_KEYCODE_3 = "10"
ADB_KEYCODE_4 = "11"
ADB_KEYCODE_5 = "12"
ADB_KEYCODE_6 = "13"
ADB_KEYCODE_7 = "14"
ADB_KEYCODE_8 = "15"
ADB_KEYCODE_9 = "16"
ADB_KEYCODE_STAR = "17"
ADB_KEYCODE_POUND = "18"
ADB_KEYCODE_DPAD_UP = "19"
ADB_KEYCODE_DPAD_DOWN = "20"
ADB_KEYCODE_DPAD_LEFT = "21"
ADB_KEYCODE_DPAD_RIGHT = "22"
ADB_KEYCODE_DPAD_CENTER = "23"
ADB_KEYCODE_VOLUME_UP = "24"
ADB_KEYCODE_VOLUME_DOWN = "25"
ADB_KEYCODE_POWER = "26"
ADB_KEYCODE_CAMERA = "27"
ADB_KEYCODE_CLEAR = "28"
ADB_KEYCODE_A = "29"
ADB_KEYCODE_B = "30"
ADB_KEYCODE_C = "31"
ADB_KEYCODE_D = "32"
ADB_KEYCODE_E = "33"
ADB_KEYCODE_F = "34"
ADB_KEYCODE_G = "35"
ADB_KEYCODE_H = "36"
ADB_KEYCODE_I = "37"
ADB_KEYCODE_J = "38"
ADB_KEYCODE_K = "39"
ADB_KEYCODE_L = "40"
ADB_KEYCODE_M = "41"
ADB_KEYCODE_N = "42"
ADB_KEYCODE_O = "43"
ADB_KEYCODE_P = "44"
ADB_KEYCODE_Q = "45"
ADB_KEYCODE_R = "46"
ADB_KEYCODE_S = "47"
ADB_KEYCODE_T = "48"
ADB_KEYCODE_U = "49"
ADB_KEYCODE_V = "50"
ADB_KEYCODE_W = "51"
ADB_KEYCODE_X = "52"
ADB_KEYCODE_Y = "53"
ADB_KEYCODE_Z = "54"
ADB_KEYCODE_COMMA = "55"
ADB_KEYCODE_PERIOD = "56"
ADB_KEYCODE_ALT_LEFT = "57"
ADB_KEYCODE_ALT_RIGHT = "58"
ADB_KEYCODE_SHIFT_LEFT = "59"
ADB_KEYCODE_SHIFT_RIGHT = "60"
ADB_KEYCODE_TAB = "61"
ADB_KEYCODE_SPACE = "62"
ADB_KEYCODE_SYM = "63"
ADB_KEYCODE_EXPLORER = "64"
ADB_KEYCODE_ENVELOPE = "65"
ADB_KEYCODE_ENTER = "66"
ADB_KEYCODE_DEL = "67"
ADB_KEYCODE_GRAVE = "68"
ADB_KEYCODE_MINUS = "69"
ADB_KEYCODE_EQUALS = "70"
ADB_KEYCODE_LEFT_BRACKET = "71"
ADB_KEYCODE_RIGHT_BRACKET = "72"
ADB_KEYCODE_BACKSLASH = "73"
ADB_KEYCODE_SEMICOLON = "74"
ADB_KEYCODE_APOSTROPHE = "75"
ADB_KEYCODE_SLASH = "76"
ADB_KEYCODE_AT = "77"
ADB_KEYCODE_NUM = "78"
ADB_KEYCODE_HEADSETHOOK = "79"
ADB_KEYCODE_FOCUS = "80"
ADB_KEYCODE_PLUS = "81"
ADB_KEYCODE_MENU = "82"
ADB_KEYCODE_NOTIFICATION = "83"
ADB_KEYCODE_SEARCH = "84"

PLAYSTORE_PACKAGE_NAME = "com.android.vending"
PLAYSTORE_MAIN_ACT = "com.google.android.finsky.activities.MainActivity"

BAD_PACKAGES = [
    ['MegaHDFilmes - Series , Filmes e Animes', 'me.filmeshd.mega'],  # App doesnt show on PlayStore...
]


LOGIN = 'Login Field'
PASSWORD = 'Password Field'
CONTINUE = 'Continue'
GOOGLE_AUTH = 'Google Auth'

IMAGE_LABELS = [
    LOGIN,
    PASSWORD,
    CONTINUE,
    GOOGLE_AUTH,
]

PACKAGE_NAMES = [
    # ['My Boy! - GBA Emulator', 'com.fastemulator.gba'],  # Purchase required, unable to install...
    # [ "Rocket League Sideswipe", "com.Psyonix.RL2D"],
    # ['Netflix', 'com.netflix.mediaclient'],  # Unable to take SS of app due to protections.
    # ['Roblox', 'com.roblox.client'],
    ['YouTube Kids', 'com.google.android.apps.youtube.kids'],
    ['Messenger', 'com.facebook.orca'],
    ['Free Fire', 'com.dts.freefireth'],
    ['Gacha Club', 'air.com.lunime.gachaclub'],
    ['Messenger Kids', 'com.facebook.talk'],
    ['Among Us!', 'com.innersloth.spacemafia'],
    ['Gacha Life', 'air.com.lunime.gachalife'],
    ['Tubi TV', 'com.tubitv'],
    ['Google Classroom', 'com.google.android.apps.classroom'],
    ['Candy Crush Soda Saga', 'com.king.candycrushsodasaga'],
    ['Google Photos', 'com.google.android.apps.photos'],
    ['Homescapes', 'com.playrix.homescapes'],
    ["June's Journey", 'net.wooga.junes_journey_hidden_object_mystery_game'],
    ['Gmail', 'com.google.android.gm'],
    ['YouTube Music', 'com.google.android.apps.youtube.music'],
    ['Viki', 'com.viki.android'],
    ['TikTok', 'com.ss.android.ugc.trill'], # Error opening with monkey com.zhiliaoapp.musically
    ['Microsoft Office Mobile', 'com.microsoft.office.officehubrow'],
    ['Spectrum TV', 'com.TWCableTV'],
    ['RAID: Shadow Legends', 'com.plarium.raidlegends'],
    ['Libby, by OverDrive Labs', 'com.overdrive.mobile.android.libby'],
    ['Google Docs', 'com.google.android.apps.docs.editors.docs'],
    ['Pluto tv', 'tv.pluto.android'],
    ['Animal Jam', 'com.WildWorks.AnimalJamPlayWild'],
    ['Webtoon', 'com.naver.linewebtoon'],
    ['PK XD', 'com.movile.playkids.pkxd'],
    ['Funimation', 'com.Funimation.FunimationNow'],
    ['myCANAL', 'com.canal.android.canal'],
    ['Picsart Ai Photo Editor', 'com.picsart.studio'],
    ['WhatsApp Business', 'com.whatsapp.w4b'],
    # ['BBC iPlayer', 'bbc.iplayer.android'],  # Not available in Region
    # ['Videoland', 'nl.rtl.videoland'], # DNExist
    ['Videoland v2', 'nl.rtl.videoland.v2'],
    # ['Ziggo GO', 'com.lgi.ziggotv'], # Not available in Region
    ['Duolingo: Learn Languages', 'com.duolingo'],
    ['Farm Heroes Saga', 'com.king.farmheroessaga'],
    ['Minecraft - Pocket Edition', 'com.mojang.minecraftpe'],
    # ['Локикрафт', 'com.ua.building.Lokicraft'], # Failed send keys
    ['Toon Blast', 'net.peakgames.toonblast'],
    ['Pokemon TCG Online', 'com.pokemon.pokemontcg'],
    ['Asphalt 8: Airborne', 'com.gameloft.android.ANMP.GloftA8HM'],
    ['8 Ball Pool', 'com.miniclip.eightballpool'],
    ['Magic Jigsaw Puzzles', 'com.bandagames.mpuzzle.gp'],
    ['Solar Smash', 'com.paradyme.solarsmash'],
    ['Jackpot Party Casino', 'com.williamsinteractive.jackpotparty'],
    ['Subway Surfers', 'com.kiloo.subwaysurf'],
    ['Episode', 'com.episodeinteractive.android.catalog'],
    ['Block Craft 3D', 'com.fungames.blockcraft'],
    ['MobilityWare Solitaire', 'com.mobilityware.solitaire'],
    ['The Sims FreePlay', 'com.ea.games.simsfreeplay_na'],
    ['ITV Player', 'air.ITVMobilePlayer'],
    ['Family Farm Adventure', 'com.farmadventure.global'],
    ['Finding Home', 'dk.tactile.mansionstory'],
    ['Sling Television', 'com.sling'],
    ['Asphalt 9: Legends', 'com.gameloft.android.ANMP.GloftA9HM'],
    ['Acellus', 'com.acellus.acellus'],
    ['Pokémon Quest', 'jp.pokemon.pokemonquest'],
    ['Guns of Glory', 'com.diandian.gog'],
    ['Bowmasters', 'com.miniclip.bowmasters'],
    ['CW Network', 'com.cw.fullepisodes.android'],
    ['Zooba', 'com.wildlife.games.battle.royale.free.zooba'],
    ['Amino: Communities and Chats', 'com.narvii.amino.master'],
    ['Solitaire Classic', 'com.freegame.solitaire.basic2'],
    ['Summoners War', 'com.com2us.smon.normal.freefull.google.kr.android.common'],
    ['Plants vs. Zombies', 'com.ea.game.pvzfree_row'],
    ['Yu-Gi-Oh! Duel Links', 'jp.konami.duellinks'],
    ['Manor Matters', 'com.playrix.manormatters'],
    ['Adorable Home', 'com.hyperbeard.adorablehome'],
    ['Spider Solitaire', 'com.spacegame.solitaire.spider'],
    ['Clip Studio Paint', 'jp.co.celsys.clipstudiopaint.googleplay'],
    ['6play', 'fr.m6.m6replay'],
    ['Rokie - Roku Remote', 'com.kraftwerk9.rokie'],
    ['Bubble Witch 3 Saga', 'com.king.bubblewitch3'],
    ['Colorscapes', 'com.artlife.coloringbook'],
    ['Spider Solitaire', 'at.ner.SolitaireSpider'],
    ['Last Day on Earth: Survival', 'zombie.survival.craft.z'],
    ['My Talking Tom Friends', 'com.outfit7.mytalkingtomfriends'],
    ['War Robots', 'com.pixonic.wwr'],
    ['Cashman Casino', 'com.productmadness.cashmancasino'],
    ['HP All in One Printer Remote', 'com.hp.printercontrol'],
    ['TeamViewer for Remote Control', 'com.teamviewer.teamviewer.market.mobile'],
    ['Best Fiends', 'com.Seriously.BestFiends'],
    ['Xodo PDF Reader & Editor', 'com.xodo.pdf.reader'],
    ['Shadow Fight 3', 'com.nekki.shadowfight3'],
    ['Chrome Browser', 'com.chrome.beta'],
    ['Audible', 'com.audible.application'],
    ['PowerDirector', 'com.cyberlink.powerdirector.DRA140225_01'],
    ['Deezer', 'deezer.android.app'],
    ['Magic Tiles 3', 'com.youmusic.magictiles'],
    ['Solitaire', 'com.brainium.solitairefree'],
    ['Classic Words', 'com.lulo.scrabble.classicwords'],
    ['Soul Knight', 'com.ChillyRoom.DungeonShooter'],
    ['Plex', 'com.plexapp.android'],
    ['Jigsaw Puzzles Epic', 'com.kristanix.android.jigsawpuzzleepic'],
    ['Extreme Car Driving Simulator', 'com.aim.racing'],
    ['Honkai Impact 3', 'com.miHoYo.bh3global'],
    ['Audiomack', 'com.audiomack'],
    ['Crossy Road', 'com.yodo1.crossyroad'],
    ['com.vanced.android.youtube', 'com.vanced.android.youtube'],
    ['TradingView', 'com.tradingview.tradingviewapp'],
    ['Slots - House of Fun', 'com.pacificinteractive.HouseOfFun'],
    ['RISK: Global Domination', 'com.hasbro.riskbigscreen'],
    ['My Boy! Free - GBA Emulator', 'com.fastemulator.gbafree'],
    ['MARVEL Strike Force', 'com.foxnextgames.m3'],
    ['com.yoku.marumovie', 'com.yoku.marumovie'],
    ['Family Farm Seaside', 'com.funplus.familyfarm'],
    ['World of Tanks Blitz', 'net.wargaming.wot.blitz'],
    ['eBay', 'com.ebay.mobile'],
    ['Count Masters - Stickman Clash', 'freeplay.crowdrun.com'],
    ['Gallery: Coloring Book', 'com.beresnevgames.gallerycoloringbook'],
    ['Krita', 'org.krita'],
    ['Adobe Lightroom', 'com.adobe.lrmobile'],
    ['com.madfut.madfut21', 'com.madfut.madfut21'],
    ['Rummikub', 'com.rummikubfree'],
    ['Chat Master!', 'com.RBSSOFT.HyperMobile'],
    # ['에픽세븐', 'com.stove.epic7.google'], Failed send keys
    ['Snake.io by Amelos Interactive', 'com.amelosinteractive.snake'],
    ['Rave', 'com.wemesh.android'],
    ['Phone Case DIY', 'com.newnormalgames.phonecasediy'],
    ['My Talking Tom 2', 'com.outfit7.mytalkingtom2'],
    ['Tag with Ryan', 'com.WildWorks.RyansTag'],
    ['Dragons: Rise of Berk', 'com.ludia.dragons'],
    ['FIFA Soccer', 'com.ea.gp.fifamobile'],
    ['Anime Center', 'pro.anioload.animecenter'],
    ['VRV', 'com.ellation.vrv'],
    ['Toca Kitchen 2', 'com.tocaboca.tocakitchen2'],
    ['Miracle Nikki', 'com.elex.nikkigp'],
    ['CrossOver on Chrome OS Beta', 'com.codeweavers.cxoffice'],
    ['Pocket Mortys', 'com.turner.pocketmorties'],
    ['Wish - Shopping Made Fun', 'com.contextlogic.wish'],
    ['Scary Teacher 3D', 'com.zakg.scaryteacher.hellgame'],
    ['FreeCell Solitaire', 'at.ner.SolitaireFreeCell'],
    ['Solitaire Card Games Free', 'com.Nightingale.Solitaire.Card.Games.Free'],
    ['250+ Solitaire Collection', 'com.anoshenko.android.solitaires'],
    ['NOOK', 'bn.ereader'],
    ['Evony', 'com.topgamesinc.evony'],
    ['Wonder Merge - Magic Merging and Collecting Games', 'com.cookapps.wonder.merge.dragon.magic.evolution.merging.wondermerge'],
    ['Wood Block Puzzle - Free Classic Block Puzzle Game', 'puzzle.blockpuzzle.cube.relax'],
    ['Hungry Shark Evolution', 'com.fgol.HungrySharkEvolution'],
    ['Mergical', 'com.fotoable.mergetown'],
    ["Diggy's Adventure", 'air.com.pixelfederation.diggy'],
    ['My Talking Angela', 'com.outfit7.mytalkingangelafree'],
    ['The Tribez', 'com.gameinsight.tribez'],
    ['Job Search', 'com.indeed.android.jobsearch'],
    ['GyaO', 'jp.co.yahoo.gyao.android.app'],
    ['Evernote', 'com.evernote'],
    ['Earn Cash & Money Rewards - CURRENT Music Screen', 'us.current.android'],
    ['Talking Tom Gold Run', 'com.outfit7.talkingtomgoldrun'],
    ['Hollywood Story', 'org.nanobit.hollywood'],
    ['hayu', 'com.upst.hayu'],
    ['NPO', 'nl.uitzendinggemist'],
    ['V – Real-time celeb broadcasting app', 'com.naver.vapp'],
    ['Cash Frenzy', 'slots.pcg.casino.games.free.android'],
    ['Crayola Scribble Scrubbie Pets', 'com.crayolallc.crayola_scribble_scrubbie_pets'],
    ['SALTO, TV & streaming illimités dans une seule app', 'fr.salto.app'],
    ['Catwalk Beauty', 'com.catwalk.fashion.star'],
    ['Mahjong Solitaire', 'com.mobilityware.MahjongSolitaire'],
    ['Pepi Tales: Kings Castle', 'com.PepiPlay.KingsCastle'],
    ['Spider Solitaire', 'com.cardgame.spider.fishdom'],
    ['Relax Jigsaw Puzzles', 'com.openmygame.games.android.jigsawpuzzle'],
    ['L.O.L. Surprise! Disco House', 'com.tutotoons.app.lolsurprisediscohouse'],
    ['100 Years - Life Simulator', 'com.lawson.life'],
    ['Mobile Legends: Adventure', 'com.moonton.mobilehero'],
    ['John GBA Lite - GBA emulator', 'com.johnemulators.johngbalite'],
    ['Egg, Inc.', 'com.auxbrain.egginc'],
    ['Heart of Vegas', 'com.productmadness.hovmobile'],
    ['Google Slides', 'com.google.android.apps.docs.editors.slides'],
    ['Jewels of Rome', 'com.g5e.romepg.android'],
    ['Cooking Diary: Tasty Hills', 'com.mytona.cookingdiary.android'],
    ['House Designer : Fix & Flip', 'com.kgs.housedesigner'],
    ['TuneIn Radio', 'tunein.player'],
    ['Video Downloader', 'video.downloader.videodownloader'],
    ['Pyramid', 'com.mobilityware.PyramidFree'],
    ['Tie Dye', 'com.crazylabs.tie.dye.art'],
    ['eFootball PES 2020', 'jp.konami.pesam'],
    ['Veezie.st - Enjoy your videos, easily.', 'st.veezie'],
    ["TV d'Orange", 'com.orange.owtv'],
    ['Prodigy Math Game', 'com.prodigygame.prodigy'],
    ['Head Ball 2', 'com.masomo.headball2'],
    ['Drive Ahead', 'com.dodreams.driveahead'],
    ['Paper Fold', 'com.game.foldpuzzle'],
    ['MetaTrader 4', 'net.metaquotes.metatrader4'],
    ['StarMaker Karaoke', 'com.starmakerinteractive.starmaker'],
    ['Cookie Jam', 'air.com.sgn.cookiejam.gp'],
    ['Nonograms Katana', 'com.ucdevs.jcross'],
    ['Kick the Buddy', 'com.playgendary.kickthebuddy'],
    ['The Simpsons™: Tapped Out', 'com.ea.game.simpsons4_na'],
    ['Tuscany Villa', 'com.generagames.toscana.hotel'],
    ['Hotel Hideaway', 'com.piispanen.hotelhideaway'],
    ['U-NEXT', 'jp.unext.mediaplayer'],
    ['DraStic DS Emulator', 'com.dsemu.drastic'],
    ['1v1.LOL', 'lol.onevone'],
    ['Sketch - Draw & Paint', 'com.sonymobile.sketch'],
    ['Merge Elves', 'com.merge.elves'],
    ['Teamfight Tactics', 'com.riotgames.league.teamfighttactics'],
    ['GlobalProtect', 'com.paloaltonetworks.globalprotect'],
    ['News Break', 'com.particlenews.newsbreak'],
    ['Shazam', 'com.shazam.android'],
    ['Bingo Frenzy! Bingo Cooking Free Live BINGO Games', 'com.cooking.bingo.ldkwh'],
    ['Kitchen Frenzy - Chef Master', 'com.biglime.cookingmadness'],
    ['Queen Bee!', 'com.MoodGames.QueenBee'],
    ['Tumblr', 'com.tumblr'],
    ['Bus Simulator : Ultimate', 'com.zuuks.bus.simulator.ultimate'],
    ['My Boy! - GBA Emulator', 'com.fastemulator.gba'],  # Purchase required, unable to install...
    ['Zeus', 'com.thezeusnetwork.www'],
    ['CATS: Crash Arena Turbo Stars', 'com.zeptolab.cats.google'],
    ['Work Chat', 'com.facebook.workchat'],
    ['Plague Inc', 'com.miniclip.plagueinc'],
    ['Sniper 3D Assassin', 'com.fungames.sniper3d'],
    ['VPN by NordVPN', 'com.nordvpn.android'],
    ['Garena Free Fire MAX', 'com.dts.freefiremax'],
    ['DAZN', 'com.dazn'],
    ['Hempire - Weed Growing Game', 'ca.lbcstudios.hempire'],
    ['Find the Difference 1000+', 'com.gamma.find.diff'],
    ['Loyverse POS - Point of Sale & Stock Control', 'com.loyverse.sale'],
    ['Daily Themed Crossword Puzzle', 'in.crossy.daily_crossword'],
    ['Age of Civilizations II', 'age.of.civilizations2.jakowski.lukasz'],
    ['globo.tv', 'com.globo.globotv'],
    ['Colorscapes Plus - Color by Number, Coloring Games', 'com.artlife.color.number.coloring.games'],
    ['Transformers: Earth Wars', 'com.backflipstudios.transformersearthwars'],
    ['Web Video Cast | Browser to TV/Chromecast/Roku/+', 'com.instantbits.cast.webvideo'],
    ['Plurall', 'com.kongros.plurall'],
    ['Spades Royale', 'com.bbumgames.spadesroyale'],
    ['TextingStory', 'com.textingstory.textingstory'],
    ['My PlayHome Plus', 'com.playhome.plus'],
    ['Flipboard', 'flipboard.app'],
    ['Cross Stitch', 'com.inapp.cross.stitch'],
    ['Who is? Brain Teaser & Riddles', 'com.unicostudio.whois'],
    ['thinkorswim', 'com.devexperts.tdmobile.platform.android.thinkorswim'],
    ['Slots Casino Games by Huuuge', 'com.huuuge.casino.slots'],
    ['Mahjong', 'com.fenghenda.mahjong'],
    ['Galaxy Attack: Alien Shooter', 'com.alien.shooter.galaxy.attack'],
    ['Madden NFL 21 Mobile Football', 'com.ea.gp.maddennfl21mobile'],
    ['Bubble Shooter Rainbow - Shoot & Pop Puzzle', 'com.blackout.bubble'],
    ['VIDEOMEDIASET', 'it.fabbricadigitale.android.videomediaset'],
    ['Google Earth', 'com.google.earth'],
    ['Viaplay', 'com.viaplay.android'],
    ['Lifetime', 'com.aetn.lifetime.watch'],
    ['Coloring Book - Color by Number & Paint by Number', 'com.iceors.colorbook.release'],
    ['Tongits Go', 'com.tongitsgo.play'],
    ['Gospel Library', 'org.lds.ldssa'],
    ['Brain Test 2: Tricky Stories', 'com.unicostudio.braintest2new'],
    ['Kingdom Rush', 'com.ironhidegames.android.kingdomrush'],
    ['Grand Theft Auto: San Andreas', 'com.rockstargames.gtasa'],
    ['Vegas Live Slots', 'com.purplekiwii.vegaslive'],
    ['MLB Perfect Inning Live', 'com.gamevilusa.mlbpilive.android.google.global.normal'],
    ['OfficeSuite 7', 'com.mobisystems.office'],
    ['Cookie Run: Kingdom - Kingdom Builder & Battle RPG', 'com.devsisters.ck'],
    ['School Girls Simulator', 'com.Meromsoft.SchoolGirlsSimulator'],
    ['SiriusXM', 'com.sirius'],
    ['Castle Solitaire: Card Game', 'com.mobilityware.CastleSolitaire'],
    ['Word Stacks', 'com.peoplefun.wordstacks'],
    # ['com.roku.trc', 'com.roku.trc'],  #  Invalid package name
    ['Albion Online', 'com.albiononline'],
    ['Time Princess: Story Traveler', 'com.igg.android.dressuptimeprincess'],
    ['Mahjong Solitaire Epic', 'com.kristanix.android.mahjongsolitaireepic'],
    ['Farm Land: Farming Life Game', 'com.loltap.farmland'],
    ['Lost Island: Blast Adventure', 'com.plarium.blast'],
    ['FNF Music Battle: Original Mod', 'com.os.falcon.fnf.battle.friday.night.funkin'],
    ['Stumble Guys: Multiplayer Royale', 'com.kitkagames.fallbuddies'],
    ['discovery+', 'com.discovery.dplay'], # com.discovery.discoveryplus is the disccovery+ package name. This OG package name is NA in region
    ['Sonos', 'com.sonos.acr2'],
    ['Binge', 'au.com.streamotion.ares'],  # NA ion Pixel 2
    ['Wordfeud', 'com.hbwares.wordfeud.free'],
    ['Farming Simulator 16', 'com.giantssoftware.fs16'],
    ['Piano Kids - Music & Songs', 'com.orange.kidspiano.music.songs'],
    # ['FreeCell', 'com.hapogames.FreeCell'],  # Invalid package name
    ['Word Cookies!', 'com.bitmango.go.wordcookies'],
    ['Floor Plan Creator', 'pl.planmieszkania.android'],
    ['Legión Anime Tema Oscuro', 'aplicaciones.paleta.alterlegionanime'],  # Fialst o send keys
    ['Adobe Illustrator Draw', 'com.adobe.creativeapps.draw'],  # NA on Pixel 2 
    ['aquapark.io', 'com.cassette.aquapark'],
    ['Bridge Race', 'com.Garawell.BridgeRace'],
    ['Jewels Magic: Mystery Match3', 'com.bitmango.go.jewelsmagicmysterymatch3'],
    ['LogMeIn Pro', 'com.logmein.ignitionpro.android'],
    ['Roku Remote: RoSpikes (WiFi&', 'roid.spikesroid.roku_tv_remote'],
    ['Battle of Warships', 'com.CubeSoftware.BattleOfWarships'],
    ['Mini Block Craft', 'mini.block.craft.free.mc'],
    ['AmongLock - Among Us Lock Screen', 'amonguslock.amonguslockscreen.amonglock'],
    ['Bloons Monkey City', 'com.ninjakiwi.monkeycity'],
    ['Match Triple 3D - Match 3D Master Puzzle', 'and.lihuhu.machingtriple'],
    # ['Showmax', 'com.showmax.app'],  # NA in region
    ['Pocket Cine Pro', 'com.flix.Pocketplus'],
    ['Guess Their Answer', 'com.qoni.guesstheiranswer'],
    ['Gold and Goblins: Idle Digging', 'com.redcell.goldandgoblins'],
    ['My Home Design - Luxury Interiors', 'com.cookapps.ff.luxuryinteriors'],
    ['Bingo Pop', 'com.uken.BingoPop'],
    ['GoToMeeting', 'com.gotomeeting'],
    ['Solitaire Collection', 'com.cardgame.collection.fishdom'],
    ['Hello Neighbor', 'com.tinybuildgames.helloneighbor'],
    ['Airport City', 'com.gameinsight.airport'],
    ['Need for Speed No Limits', 'com.ea.game.nfs14_row'],
    ['BBC Sounds', 'com.bbc.sounds'],
    ['Rummy 500', 'com.trivialtechnology.Rummy500D'],
    ['Sweet Dance', 'com.au.dance.en'],
    ['Papers Grade Please!', 'com.hyperdivestudio.papersgradeplease'],
    ['Board Kings', 'com.jellybtn.boardkings'],
    ['Dan The Man', 'com.halfbrick.dantheman'],
    ['[3D Platformer] Super Bear Adventure', 'com.Earthkwak.Platformer'],
    ['Kayo Sports', 'au.com.kayosports'],
    ['DoubleDown Casino', 'com.ddi'],
    ['Bingo Story', 'com.clipwiregames.bingostory'],
    ['Color By Number For Adults', 'com.pixign.premium.coloring.book'],
    ['Fox News', 'com.foxnews.android'],
    ['Rider', 'com.ketchapp.rider'],
    ['Kobo', 'com.kobobooks.android'],
    ['Funky Bay', 'com.belkatechnologies.fe'],
    ['WATCHED', 'com.watched.play'],
    ['Classic Solitaire', 'com.solitaire.card'],
    ['Chess Free', 'uk.co.aifactory.chessfree'],
    ['M64Plus FZ Emulator', 'org.mupen64plusae.v3.fzurita'],
    ['Bubble Shooter by Ilyon', 'bubbleshooter.orig'],
    ['Blockman Go', 'com.sandboxol.blockymods'],
    ['TLC GO', 'com.discovery.tlcgo'],
    ['DAFU Casino', 'com.grandegames.slots.dafu.casino'],
    ['Cookie Jam Blast', 'air.com.sgn.cookiejamblast.gp'],
    ['Investigation Discovery GO', 'com.discovery.idsgo'],
    # ['Contacts', 'com.google.android.contacts'], # Unable to uninstall, default app?
    ['FanFiction.Net', 'com.fictionpress.fanfiction'],
    ['Eerskraft', 'com.eers.kraft.eerskraft'],
    ['CW Seed on Fire TV', 'com.cw.seed.android'],
    ['Solitaire - Free Classic Solitaire Card Games', 'beetles.puzzle.solitaire'],
    ['combyne', 'com.combyne.app'],
    ['PlanetCraft: Block Craft Games', 'com.craftgames.plntcrft'],
    ['BanG Dream', 'com.bushiroad.en.bangdreamgbp'],
    ['Mini World Block Art', 'com.playmini.miniworld'],
    ['Omlet Arcade', 'mobisocial.arcade'],
    ['ArtFlow: Paint Draw Sketchbook', 'com.bytestorm.artflow'],
    ['World War Heroes', 'com.gamedevltd.wwh'],
    ['Horse Haven World Adventures', 'com.ubisoft.horsehaven.adventures'],
    ['Heroes Inc!', 'com.blueflamingo.herolab'],
    ['Dancing Road: Colour Ball Run', 'com.amanotes.pamadancingroad'],
    ['Groundworks G3', 'com.groundworkcompanies.g3'],
    ['Solitaire', 'solitaire.card.games.klondike.solitaire.classic.free'],
    ['AndrOpen Office', 'com.andropenoffice'],
    ['Tapastic', 'com.tapastic'],
    ['KakaoTalk', 'com.kakao.talk'],
    ['Shadow Fight 2', 'com.nekki.shadowfight'],
    ['Red Ball 4', 'com.FDGEntertainment.redball4.gp'],
    ['Polaris Office', 'com.infraware.office.link'],
    ['Granny 3', 'com.DVloper.Granny3'],
    ['Fios TV', 'com.verizon.fios.tv'],
    ['Duskwood - Crime & Investigation Detective Story', 'com.everbytestudio.interactive.text.chat.story.rpg.cyoa.duskwood'],
    ['The Battle of Polytopia', 'air.com.midjiwan.polytopia'],
    ['Moments: Choose Your Story', 'com.gg.lovestory.moments'],
    ['Acrylic Nails!', 'com.crazylabs.acrylic.nails'],
    ['Hello Kitty Nail Salon', 'com.budgestudios.HelloKittyNailSalon'],
    ['Onnect', 'com.gamebility.onet'],
    ['Whats Web', 'com.softinit.iquitos.whatsweb'],
    ['PokerStars Poker', 'com.pyrsoftware.pokerstars.net'],
    ['Telegram', 'org.thunderdog.challegram'],
    ['DOFUS Touch', 'com.ankama.dofustouch'],
    ['Steam Link', 'com.valvesoftware.steamlink'],
    ['Monster Strike', 'jp.co.mixi.monsterstrike'],
    ['House Flipper: Home Design & Simulator Games', 'com.imaginalis.HouseFlipperMobile'],
    ['Grand Hotel Mania', 'com.deuscraft.TurboTeam'],
    ['Nick Jr.', 'com.nick.android.nickjr'],
    # ['Whats Web Scan', 'com.softinit.iquitos.whatswebscan'], # NA on Playstore
    ["Hide 'N Seek!", 'com.seenax.HideAndSeek'],
    ['Ball Run 2048', 'com.kayac.ball_run'],
    ['Manor Cafe', 'com.gamegos.mobile.manorcafe'],
    ['Disney Magic Kingdoms', 'com.gameloft.android.ANMP.GloftDYHM'],
    ['Solitaire', 'com.agedstudio.card.solitaire.klondike'],
    ['WATCH ABC', 'com.disney.datg.videoplatforms.android.abc'],
    ['YouTube', 'com.google.android.youtube'],
    ['Google Drive', 'com.google.android.apps.docs'],
    ['Google Keep', 'com.google.android.keep'],
    ['Google Maps', 'com.google.android.apps.maps'],
    ['Toontastic 3D', 'com.google.toontastic'],
    ['Google Chat', 'com.google.android.apps.dynamite'],
    ['Youtube Music', 'com.google.android.apps.youtube.music.pwa'],
    ['Files by Google: Clean up space on your phone', 'com.google.android.apps.nbu.files'],
    ['YouTube Creator Studio', 'com.google.android.apps.youtube.creator'],
    ['"Youtube Music'],
    ['(Google Play Music)"', 'com.google.android.music'],
    ['Google Tasks: Any Task Any Goal. Get Things Done', 'com.google.android.apps.tasks'],
    ['Chrome Remote Desktop', 'com.google.chromeremotedesktop'],
    ['Google PDF Viewer', 'com.google.android.apps.pdfviewer'],
    ['Jamboard', 'com.google.android.apps.jam'],
    ['Google Find My Device', 'com.google.android.apps.adm'],
    ['Google Family Link for children & teens', 'com.google.android.apps.kids.familylinkhelper'],
    ['Google One', 'com.google.android.apps.subscriptions.red'],
    ['Gallery Go by Google Photos', 'com.google.android.apps.photosgo'],
    ['Google My Business', 'com.google.android.apps.vega'],
    ['Google Opinion Rewards', 'com.google.android.apps.paidtasks'],
]


TOP_500_APPS = PACKAGE_NAMES[:500]
