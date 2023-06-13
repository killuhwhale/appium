import os
from typing import List
from bs4 import BeautifulSoup
from time import time
import requests
import concurrent.futures

def get_app_name(package_name: str) -> str:
    url = f'https://play.google.com/store/apps/details?id={package_name}'
    response = requests.get(url, timeout=5)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        error_section = soup.find('div', {'id': 'error-section'})
        if error_section and error_section.text == "We're sorry, the requested URL was not found on this server.":
            return "Invalid app"

        name_span_parent = soup.find('h1', {'itemprop': 'name'})
        name_span = name_span_parent.findChild('span')
        if name_span:
            return name_span.text

    return "Name not found"


def process_package(pkg: str) -> str:
    name = get_app_name(pkg)
    return f"{name}\t{pkg}"


def run(app_list: List[str]):
    """Takes a list of package names and returns a list of appName\tpackageName."""
    username = os.getenv('USER')
    file_path = f"/home/{username}/new_app_list.tsv"

    with open(file_path, "w") as f:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit each package processing as a separate task
            future_results = [executor.submit(process_package, pkg) for pkg in app_list]

            # Write the results to the file as they become available
            for future in concurrent.futures.as_completed(future_results):
                result = future.result()
                f.write(f"{result}\n")

    print(f"Finished, see file here: {file_path}")


if __name__ == '__main__':
    apps = """com.rubygames.hunterassassin2
com.halfbrick.fruitninjax
com.frivolition.daysbygone
com.pgstudio.heroadventure
com.loongcheer.neverlate.wizardlegend.fightmaster
com.ldw.cooking
com.EOAG.BankruptDevil
net.wooga.junes_journey_hidden_object_mystery_game
com.tinyco.potter
org.nanobit.hollywood
com.upjers.zoo2animalpark
com.mytona.seekersnotes.android
air.com.pixelfederation.diggy
com.fivebn.lt1.f2p
com.bandagames.miner
com.LiliJoy.DragonLand
com.g5e.crimemysteries.android
com.gameinsight.explorelands
com.trickytribe.tinkerisland2
com.g5e.thehiddentreasurespg.android
com.sigono.heaven01
com.halfbrick.jetpackjoyride
com.cookingmaster.restaurant.fever.chef.kitchen.free
pl.idreams.SkyForceReloaded2016
game.naga.fishing.world
com.Wind.wings.Space.Shooter
com.teestudio.bricksnballs.breakerquest
co.imba.archero
com.appxplore.clawstars
com.gamovation.mahjongclub
com.rummikubfree
air.com.beachbumgammon
and.lihuhu.MTBall
chessfriends.online.chess
com.sngict.okeyextra
com.bingo.wild.android
com.uken.BingoPop
com.mola.playspace.android.parchis
net.backgammonstars.android
air.com.glidingdeer.bingodrivemobile
net.skillcap.farkle
com.boundless.jawaker
com.mattel163.phase10
com.jogatina.buraco
com.trucovamos.play
com.playjoygame.pg
com.playshoo.texaspoker.romania
com.iscoolentertainment.belote
com.badambiz.saubaloot
com.wonderpeople.megahitpoker.global
com.me2zen.tripeaks.v4.and
com.ste.android.schnopsnfree
com.epochalstorm.scopa
com.gameindy.dummyth
com.MangoSoft.Susun
com.bbumgames.spadesroyale
gp.farm.harvest.solitaire.tripeaks
com.exoty.tarot
com.uken.solitaire.story
com.avid.cue
com.zcmxd.pokergaga
com.stickyhands.farmville
com.trivialtechnology.Rummy500D
com.gotogames.funbridge
com.Everguild.HorusHeresy
games.wellplayed.apocalypse.android
com.gameduell.gin.rummy.card.game
com.MadStudios.SolitaireFairytaleDev
com.productmadness.lightninglink
com.ddi
com.williamsinteractive.goldfish
com.userjoy.LetsVegasSlots
com.igs.goldentigerslots
linkdesks.pop.bubblegames.bubbleshooter
com.Seriously.BestFiends
com.superplaystudios.dicedreams
com.cookie.match3.casual
com.playgendary.homes
com.foranj.farmtown
puzzle.merge.hotel.empire
com.playday.game.medievalFarm.android
air.net.ideasam.games.cat
com.homedesign.babymanor.virtual.free
com.zymobile.space.apartment
com.zymobile.journey.decor
com.zymobile.dream.island
bg.xssoftware.ladypopular.fashionarena
com.spyke.royalriches
com.kingone.puzzle.gemking
com.joycastle.mergematch
com.mybogames.merge
net.happywit.piratelife
com.zymobile.dream.houseboat
puzzle.merge.family.mansion
com.standegg.mergedesign
games.sugarfree.glammdfashiondressup.free
com.qhdjgkj.coinpet
com.ivy.merge
com.fuseboxgames.loveisland.match3.gp
com.dragons.tokens.crypto
com.concretesoftware.idlegamearcade
com.yurukita.game
com.miniit.difference
com.runawayplay.flutter
com.rockstonedev.bottle
com.carefree.game.merge.animals
com.skillgames.JewelMatchJourney
com.easybrain.block.puzzle.games
com.playflock.family.hotel.story.home.mansion.puzzle.garden.decoration
com.redemptiongames.sugar
com.pixodust.games.free.rpg.medieval.merge.puzzle.empire
com.g5e.sherlock.android
com.Trailmix.LoveAndPiesMerge
com.narcade.farm_bubbles_bubble_shooter
com.mf.town
com.disney.emojimatch_goo
com.zymobile.dream.home
com.loop.matchtile3d
com.TwoDesperados.WokaWoka
com.mugshotgames.slidingseas
com.purplekiwii.mb
org.smapps.find
com.outplayentertainment.chefblast
com.zymobile.restaurant
com.pixelfederation.solve.mystery.puzzle.adventure
com.soulgame.idlePrimitive
com.mergeland.animal.adventure.island
com.disney.maleficent_goo
air.com.and.games505.gemsofwar
com.ejoy.sea
com.morechili.mergeelf
air.com.qublix.tropictrouble
com.hive.peko
jp.wonderplanet.CrashFever
com.merge.farmtown
air.com.sublinet.tastytale
com.fwaygames.lostmerge
air.com.qublix.forestrescuetwo
air.com.remivision.DreamlandStory
com.fenomen.redhoodf2p
air.com.qublix.bubblerescue
air.com.playforia.iq.bubbles.android
com.Cratoonz.CatHeroes
com.valasmedia.bubblecloudplanet
com.lagoonsoft.pb
com.ember.meowmatch
com.mob.crowd.arena.wars
co.tamatem.fashionqueen
com.ea.game.starwarscapital_row
com.pabloleban.IdleSlayer
com.makingfun.mageandminions
com.whaleapp.blitz.rise.heroes.idle.rpg.battle
com.aigrind.warspear
com.ubisoft.accovenant
com.ftt.msleague_gl
air.com.r2gamesusa.clickerheroes
com.kurechii.postknight2
com.gamesture.questland
com.komoe.fsgp
com.libii.dressupworld
com.highbrow.games.dvarena
com.superplanet.goddungeon
com.beesquare.almostahero
com.special.warshiplegend.idle.asia
com.n3twork.legendary
com.playsome.friendsanddragons
com.fluffyfairygames.idleminertycoon
com.lumber.inc
com.ea.game.simcitymobile_row
com.redcell.goldandgoblins
com.advant.streamer
com.bethsoft.falloutshelter
conquer.the.tower.castle.battle
com.farmadventure.global
com.codigames.idle.prison.empire.manager.tycoon
com.gamegos.mobile.cafeland
com.Sarepta.MyChild
com.sparklingsociety.cityisland5
com.behefun.homemhmg
com.style.fashion.game.suitsme
air.com.pixelfederation.TrainStationGame
com.hyperbeard.odyssey
com.gamegos.adventure.bay.paradise.farm
com.mysterytag.paris
com.supersolid.spark
com.handsomeoldtree.idlefirefightertycoon
com.volka.taonga
com.kolibrigames.idlerestauranttycoon
com.gameinsight.tribez
com.gametown.hotel.madness
com.lavaflame.MMO
risk.city.dominations.strategy.io.games
com.fathermade.catisland
com.excitedowlarts.idlehighschooltycoon
com.likeitgames.AfterRain2
com.newvoy.cookingvoyage.android
com.mafgames.idle.cat.neko.manager.tycoon
ru.overmobile.tower
com.yboga.dreamhospital
com.supersolid.honestfood
com.lucky.rankinsignia
com.nixhydragames.thearcana
com.creativemobile.zc
com.mobilfactory.gqlton
ru.crazypanda.ZombieShop
com.domobile.game.evolution
com.bucketplay.mylittleparadise
com.pixowl.addams
com.sparklingsocietysims.towncitybrawlworldofbrawlers
com.grampus.cookingadventure
com.ivmob.interior
com.codigames.university.empire.idle.tycoon
com.TironiumTech.IdlePlanetMiner
com.TechTreeGames.IdleBrickBreaker
com.Enixan.Homestead
com.colyinc.standMyHeroes
com.interactive.novella
love.journey.episode.luv
com.mujoy.wysdx.tw
games.tinycloud.tinyshop
com.horagames.cryptominer
com.Kraken.TinyWorlds
com.fastpoodlegames.idletaxitycoon
com.boombitgames.Dartsy
cricketgames.hitwicket.strategy
com.giraffegames.pool
com.frogmind.rumblestars
com.playmister
com.trophymanager.pro11
com.galasports.football
com.Per.DiscGolf
com.powerplaymanager.athleticsmaniagames
com.trophymanager.ultra
com.trophymanager.wsm
com.yottagames.gameofmafia
com.socialquantum.acityint
com.leme.coe
com.dragonplus.cookingfrenzy
com.funplus.kingofavalon
com.easytech.wc3
com.pixelfederation.portcity.ship.tycoon.strategy.simulation
heroes.battle.strategy.card.game
com.geewa.smashingfour
com.dreamotion.roadtovalor
air.com.goodgamestudios.empirefourkingdoms
com.ftxgames.narcos
com.panoramik.autochess
air.com.pixelfederation.seaport.explore.collect.trade
com.gtarcade.ioe.global
com.zillionwhales.mushroomwars2
heroes.of.war
com.millionvictories.games.millionlords
com.kingsgroup.ww2
com.seal.outlaws
com.easytech.rome.android
com.kixeye.wcm
com.onemoregame.leagueofxenoduck
com.dragonest.autochess.google
com.erepubliklabs.worldatwar
com.babeltimeus.legendstd
com.topgamesinc.zombies
com.easytech.iron.android
com.nordeus.heroic
com.allstarunion.mw3
com.indie.shj.google.en
com.kongregate.mobile.stormbound.google
com.generagames.gladiatorheroes
com.loadcomplete.mergedefense
com.erepubliklabs.one
com.easytech.ew5.android
com.bitmango.go.wordcookies
com.gsr.wordcross
com.crossword.bible.cookies.find.english
com.nytimes.crossword
com.dailyword.challenge.addictive
word.card.games.g
"""
    start = time()
    run(apps.split("\n"))
    print(f"Took: {time() - start}s")