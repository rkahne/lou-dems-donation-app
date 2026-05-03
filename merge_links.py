import json

links_data = {
  "Joshua Blanton": {"actblue_url": None, "website_url": "https://joshuablantonsr.com/", "facebook_url": None, "twitter_url": "https://x.com/JoshuaBlantonSr", "instagram_url": None},
  "Charles Booker": {"actblue_url": "https://secure.actblue.com/donate/charles-booker-3", "website_url": "https://charlesbooker.org/", "facebook_url": "https://www.facebook.com/Booker4KY/", "twitter_url": "https://twitter.com/Booker4KY", "instagram_url": "https://www.instagram.com/booker4ky/"},
  "Logan Forsythe": {"actblue_url": "https://secure.actblue.com/donate/logan-forsythe-1", "website_url": "https://loganforsythe.com/", "facebook_url": "https://www.facebook.com/loganforsytheky", "twitter_url": "https://x.com/loganforky", "instagram_url": "https://www.instagram.com/loganforsytheky/"},
  "Amy McGrath": {"actblue_url": "https://secure.actblue.com/donate/amy-mcgrath-2", "website_url": "https://amymcgrath.com/", "facebook_url": "https://www.facebook.com/AmyMcGrathKY", "twitter_url": "https://twitter.com/AmyMcGrathKY", "instagram_url": "https://www.instagram.com/amymcgrathky/"},
  "Dale Romans": {"actblue_url": "https://secure.actblue.com/donate/dale-romans-1", "website_url": "https://daleromans.com/", "facebook_url": "https://www.facebook.com/daleforkentucky", "twitter_url": "https://x.com/DaleRomansKY", "instagram_url": "https://www.instagram.com/daleromans/"},
  "Pamela Stevenson": {"actblue_url": "https://secure.actblue.com/donate/pamela-stevenson-1", "website_url": "https://www.stevensonforsenate.com/", "facebook_url": "https://www.facebook.com/PamForAG/", "twitter_url": "https://x.com/ColPamStevenson", "instagram_url": "https://www.instagram.com/colpamstevenson"},
  "Vincent Thompson": {"actblue_url": "https://secure.actblue.com/donate/vincentthompsoncampaignfund", "website_url": None, "facebook_url": "https://www.facebook.com/vincentanthonythompson2026ussenate/", "twitter_url": None, "instagram_url": None},
  "Morgan McGarvey": {"actblue_url": "https://secure.actblue.com/donate/bs_mcg_web_fr", "website_url": "https://www.morganmcgarvey.com/", "facebook_url": "https://www.facebook.com/MorganMcGarveyForCongress", "twitter_url": "https://twitter.com/MorganMcGarvey", "instagram_url": "https://www.instagram.com/morgan_mcgarvey/"},
  "William Dakota Compton": {"actblue_url": "https://secure.actblue.com/donate/compton4congress2026", "website_url": "https://www.williamcompton.com", "facebook_url": "https://www.facebook.com/Compton4KY2024/", "twitter_url": "https://x.com/compton4ky2022", "instagram_url": "https://www.instagram.com/compton4ky2026/"},
  "David Hatfield": {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Hank Linderman": {"actblue_url": None, "website_url": "https://www.hank4ky.com/", "facebook_url": "https://www.facebook.com/hank4ky/", "twitter_url": "https://twitter.com/hank4ky", "instagram_url": None},
  "Megan Wingfield": {"actblue_url": "https://secure.actblue.com/donate/megan-wingfield-1", "website_url": "https://meganwingfieldforcongress.com/", "facebook_url": "https://www.facebook.com/megan.wingfield.for.congress/", "twitter_url": "https://twitter.com/megan_wingfield", "instagram_url": "https://www.instagram.com/megannwingfieldd/"},
  "Christian Furman": {"actblue_url": "https://secure.actblue.com/donate/christian-furman", "website_url": "https://christianforky.com/", "facebook_url": "https://www.facebook.com/christianforky", "twitter_url": "https://x.com/christianforky", "instagram_url": "https://www.instagram.com/christianforky"},
  "Chaz Stoess": {"actblue_url": "https://secure.actblue.com/donate/chazstoess", "website_url": "https://chazforky.com/", "facebook_url": "https://www.facebook.com/chaz4ky", "twitter_url": None, "instagram_url": "https://www.instagram.com/chazforky/"},
  "Keturah Herron": {"actblue_url": "https://secure.actblue.com/donate/keturah-herron-for-state-senate", "website_url": "https://www.keturahherron.com/", "facebook_url": "https://www.facebook.com/KeturahHerronforKYSenate/", "twitter_url": "https://twitter.com/KeturahHerron", "instagram_url": "https://www.instagram.com/keturah.herron/"},
  "Sarah Cole McIntosh": {"actblue_url": "https://secure.actblue.com/donate/scm-website", "website_url": "https://www.sarahcolemcintosh.com/", "facebook_url": None, "twitter_url": "https://x.com/SarahColeMcInt1", "instagram_url": None},
  "Luke Whitehead": {"actblue_url": "https://secure.actblue.com/donate/luke-whitehead-1", "website_url": "https://whiteheadforsenate.com/", "facebook_url": "https://www.facebook.com/LukeWhitehead24/", "twitter_url": None, "instagram_url": "https://www.instagram.com/luke_whitehead24/"},
  "Gary Clemons": {"actblue_url": "https://secure.actblue.com/donate/gary-clemons-1", "website_url": "https://garyclemons.com/", "facebook_url": "https://www.facebook.com/GaryClemonsForSenate37", "twitter_url": None, "instagram_url": "https://www.instagram.com/garyclemonssenate37/"},
  "Karen Berg": {"actblue_url": "https://secure.actblue.com/donate/kysdcccwebsite", "website_url": "https://karenforkentucky.com/", "facebook_url": "https://www.facebook.com/StateSenatorKarenBerg/", "twitter_url": "https://twitter.com/karenforky", "instagram_url": None},
  "Almaria Baker": {"actblue_url": "https://secure.actblue.com/donate/team-baker-1", "website_url": "https://www.bakerforhouse28.com/", "facebook_url": "https://www.facebook.com/people/Baker-for-State-House-D-28/61556897897015/", "twitter_url": None, "instagram_url": None},
  "Cassie Blausey": {"actblue_url": "https://secure.actblue.com/donate/cassieblausey", "website_url": "https://cassieblausey.com/", "facebook_url": "https://www.facebook.com/cassieblausey", "twitter_url": "https://x.com/cassieblausey", "instagram_url": "https://www.instagram.com/cassieblausey/"},
  "Daniel Grossberg": {"actblue_url": "https://secure.actblue.com/donate/repgrossberg", "website_url": "https://www.grossberg4ky.com/", "facebook_url": "https://www.facebook.com/grossberg4ky", "twitter_url": "https://twitter.com/grossberg4ky", "instagram_url": "https://www.instagram.com/grossberg4ky/"},
  "Cassie Lyles": {"actblue_url": "https://secure.actblue.com/donate/cassie-lyles-1", "website_url": "https://cassielyles.com/", "facebook_url": "https://www.facebook.com/profile.php?id=61575024633957", "twitter_url": None, "instagram_url": "https://www.instagram.com/cassielyles4kyhouse30/"},
  "Max Morley": {"actblue_url": None, "website_url": "https://www.maxforky.com/", "facebook_url": "https://www.facebook.com/profile.php?id=61569505973325", "twitter_url": "https://x.com/maxwellmorley", "instagram_url": "https://www.instagram.com/maxforky/"},
  "Mitra Subedi": {"actblue_url": "https://secure.actblue.com/donate/elect-mitra-subedi-as-state-representative-1", "website_url": "https://www.subedihouse30.com/", "facebook_url": "https://www.facebook.com/p/Mitra-Subedi-61556215592834/", "twitter_url": None, "instagram_url": None},
  "Tim Hall": {"actblue_url": "https://secure.actblue.com/donate/tim-hall-1", "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Tina Bojanowski": {"actblue_url": "https://secure.actblue.com/donate/tinaforkentucky", "website_url": "https://www.tinaforkentucky.com/", "facebook_url": "https://www.facebook.com/tinaforkentucky/", "twitter_url": "https://x.com/tinaforkentucky", "instagram_url": "https://www.instagram.com/tinaforkentucky/"},
  "Jennifer Hardin": {"actblue_url": "https://secure.actblue.com/donate/jennifer-hardin-1", "website_url": "https://www.hardin4ky.com/", "facebook_url": "https://www.facebook.com/hardin4ky/", "twitter_url": None, "instagram_url": "https://www.instagram.com/hardin4ky/"},
  "Tarah Combs LeBlanc": {"actblue_url": "https://secure.actblue.com/donate/tarahforky", "website_url": "https://tarahforky.com/", "facebook_url": "https://www.facebook.com/profile.php?id=61584679924878", "twitter_url": None, "instagram_url": "https://www.instagram.com/tarahforky/"},
  "Sarah Stalker": {"actblue_url": None, "website_url": "https://www.sarahforky.com/", "facebook_url": "https://www.facebook.com/SarahStalkerforKY", "twitter_url": "https://x.com/sarahforky", "instagram_url": "https://www.instagram.com/sarahforky/"},
  "Lisa Willner": {"actblue_url": None, "website_url": "https://lisawillner.com/", "facebook_url": "https://www.facebook.com/lisaforkyhouse/", "twitter_url": "https://x.com/lgwillner", "instagram_url": None},
  'William "Woody" Zorn': {"actblue_url": "https://secure.actblue.com/donate/zornky36", "website_url": None, "facebook_url": "https://www.facebook.com/Woody4KY/", "twitter_url": "https://x.com/woodyzorn", "instagram_url": "https://www.instagram.com/woody4ky/"},
  "Rachel Roarx": {"actblue_url": "https://secure.actblue.com/donate/committee-to-elect-rachel-roarx-1", "website_url": "https://rachelroarx.com/", "facebook_url": "https://www.facebook.com/rachelroarxdistrict38/", "twitter_url": "https://x.com/RachelRoarx", "instagram_url": "https://www.instagram.com/rachelroarxdistrict38/"},
  "Patrick Bryant Dunegan": {"actblue_url": "https://secure.actblue.com/donate/patrick-dunegan-1", "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Nima Kulkarni": {"actblue_url": None, "website_url": "https://www.votenima.com/", "facebook_url": "https://www.facebook.com/StateRepresentativeNimaKulkarni/", "twitter_url": "https://x.com/RepNimaKulkarni", "instagram_url": "https://www.instagram.com/repnimakulkarni/"},
  "Mary Lou Marzian": {"actblue_url": "https://secure.actblue.com/donate/state-campaign-fund-for-mary-marzian-1", "website_url": None, "facebook_url": "https://www.facebook.com/RepMLMarzian", "twitter_url": "https://x.com/MaryLouMarzian", "instagram_url": None},
  "Joshua Watkins": {"actblue_url": "https://secure.actblue.com/donate/re-elect-watkins-for-42", "website_url": "https://votejoshuawatkins.com/", "facebook_url": "https://www.facebook.com/joshua4kentucky/", "twitter_url": None, "instagram_url": "https://www.instagram.com/joshua4kentucky/"},
  "Robert LeVertis Bell": {"actblue_url": "https://secure.actblue.com/donate/robert-levertis-bell-1", "website_url": "https://bell4ky.com/", "facebook_url": "https://www.facebook.com/bell4ky/", "twitter_url": "https://twitter.com/bell4ky", "instagram_url": "https://www.instagram.com/robertlevertisbell/"},
  "Joi McAtee": {"actblue_url": "https://secure.actblue.com/donate/joi-mcatee-1", "website_url": "https://joimcatee.com/", "facebook_url": "https://www.facebook.com/joiforkentucky/", "twitter_url": None, "instagram_url": "https://www.instagram.com/joiforkentucky/"},
  "Beverly Chester-Burton": {"actblue_url": "https://secure.actblue.com/donate/bcb4ky", "website_url": None, "facebook_url": "https://www.facebook.com/bcb4ky/", "twitter_url": None, "instagram_url": None},
  "Jesten S. Slaw": {"actblue_url": "https://secure.actblue.com/donate/slawforky", "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Kenya Wade": {"actblue_url": "https://secure.actblue.com/donate/winwithwade.com", "website_url": "https://kenyaforkentucky.com/", "facebook_url": "https://www.facebook.com/kenyaforkentucky/", "twitter_url": None, "instagram_url": None},
  "Al Gentry": {"actblue_url": "https://secure.actblue.com/donate/al-gentry", "website_url": "https://www.algentryforkentucky.com/", "facebook_url": "https://www.facebook.com/kyalgentry/", "twitter_url": None, "instagram_url": None},
  "Nathan Bellows": {"actblue_url": None, "website_url": "https://nathanbellowsforky.com/", "facebook_url": "https://www.facebook.com/nathanbellowsforky/", "twitter_url": None, "instagram_url": "https://www.instagram.com/nathanbellowsforky/"},
  "Suhas Kulkarni": {"actblue_url": "https://secure.actblue.com/donate/suhas48", "website_url": "https://suhas48.com/", "facebook_url": "https://www.facebook.com/Suhas48th/", "twitter_url": None, "instagram_url": None},
  "Colleen Younger": {"actblue_url": None, "website_url": "https://youngerforlouisvillepva.org", "facebook_url": "https://www.facebook.com/ColleenYoungerforPVA/", "twitter_url": None, "instagram_url": None},
  "Queenie Averette": {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Sarah Martin": {"actblue_url": None, "website_url": "https://votesarahmartin.com", "facebook_url": "https://www.facebook.com/votesarahmartin", "twitter_url": "https://x.com/votesarahmartin", "instagram_url": "https://www.instagram.com/votesarahmartin/"},
  "Karl Price": {"actblue_url": None, "website_url": "https://www.votekarlprice.com", "facebook_url": "https://www.facebook.com/votekarlprice", "twitter_url": "https://x.com/kplawlive", "instagram_url": "https://www.instagram.com/votekarlprice/"},
  'Rosalind "Roz" Welch': {"actblue_url": "https://secure.actblue.com/donate/rosalind--roz--welch-1", "website_url": "https://www.rozwelch.com", "facebook_url": "https://www.facebook.com/rozwelch5022/", "twitter_url": None, "instagram_url": "https://www.instagram.com/roz4clerk/"},
  "David Yates": {"actblue_url": "https://secure.actblue.com/donate/davidyates3", "website_url": "https://www.voteyates.com", "facebook_url": "https://www.facebook.com/electdavidyates", "twitter_url": None, "instagram_url": "https://www.instagram.com/davidyatesky37/"},
  "Richard Breen": {"actblue_url": None, "website_url": "https://www.breenforsheriff.org", "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Steve Healey": {"actblue_url": None, "website_url": "https://www.healeyforsheriff.com", "facebook_url": "https://www.facebook.com/healeyforsheriff", "twitter_url": "https://x.com/SteveHealeyKY", "instagram_url": "https://www.instagram.com/healeyforsheriff/"},
  "Stephen Yancey": {"actblue_url": "https://secure.actblue.com/donate/stephen-yancey-for-sheriff", "website_url": "https://yanceyforsheriff.com", "facebook_url": "https://www.facebook.com/p/Stephen-L-Yancey-for-Sheriff-100077841107208/", "twitter_url": None, "instagram_url": "https://www.instagram.com/stephenlyancey/"},
  "Joyce Cooper": {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Jo-Ann Farmer": {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Mera Kathryn Corlett": {"actblue_url": None, "website_url": "https://www.meracorlett.com", "facebook_url": "https://www.facebook.com/JofPMeraKCorlett", "twitter_url": None, "instagram_url": None},
  "Gary Fields": {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Christopher James Bayer": {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Shannon T. Leach": {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Monica Flowers": {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
  "Craig Greenberg": {"actblue_url": None, "website_url": "https://www.greenbergformayor.com", "facebook_url": "https://www.facebook.com/MayorCraigGreenberg/", "twitter_url": "https://x.com/LouisvilleMayor", "instagram_url": "https://www.instagram.com/mayorcraiggreenberg/"},
  "Tammy Hawkins": {"actblue_url": None, "website_url": None, "facebook_url": "https://www.facebook.com/CouncilwomanTammyHawkins/", "twitter_url": None, "instagram_url": None},
  "Kumar Rashad": {"actblue_url": "https://secure.actblue.com/donate/kumar-rashad-2", "website_url": "https://kumarforthepeople.wixsite.com/district15", "facebook_url": "https://www.facebook.com/KumarforthePeople/", "twitter_url": None, "instagram_url": None},
  "Aprile Hearn": {"actblue_url": "https://secure.actblue.com/donate/aprile-hearn-1", "website_url": "https://www.aprilehearn.org", "facebook_url": "https://www.facebook.com/share/17GgixyT2o/", "twitter_url": None, "instagram_url": "https://www.instagram.com/voteforaprilehearn/"},
  "Paula McCraney": {"actblue_url": "https://secure.actblue.com/donate/paula-mccraney-1", "website_url": "https://reelectmccraney.blog", "facebook_url": "https://www.facebook.com/PaulaMcCraneyD7/", "twitter_url": "https://x.com/PaulaMcCraneyD7", "instagram_url": None},
  "Melina Hettiaratchi": {"actblue_url": None, "website_url": "https://withmelina.com", "facebook_url": "https://www.facebook.com/kywithmelina", "twitter_url": "https://x.com/educator_esq", "instagram_url": "https://www.instagram.com/kywithmelina/"},
  "Jennifer Chappell": {"actblue_url": None, "website_url": "https://jenniferformetrocouncil.com", "facebook_url": "https://www.facebook.com/jenniferformetrocouncil", "twitter_url": "https://twitter.com/chappellfor15", "instagram_url": "https://www.instagram.com/jenniferformetrocouncil/"},
  "Markus Winkler": {"actblue_url": "https://secure.actblue.com/donate/markus-winkler-2026", "website_url": "https://winklerformetrocouncil.com", "facebook_url": "https://www.facebook.com/winklerformetrocouncil/", "twitter_url": None, "instagram_url": None},
  "Betsy Ruhe": {"actblue_url": None, "website_url": "https://www.ruheformetro21.com", "facebook_url": "https://www.facebook.com/BetsyRuhe21/", "twitter_url": None, "instagram_url": None},
  "Ainsley Jones": {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None},
}

with open(r'C:\Users\Robert\Documents\jc-dems-app\candidates.json') as f:
    data = json.load(f)

for race in data['races']:
    race['candidate_links'] = {}
    for name in race.get('democratic_primary_candidates', []):
        race['candidate_links'][name] = links_data.get(name, {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None})
    endorsed = race.get('ldp_endorsed')
    if endorsed:
        race['candidate_links'][endorsed] = links_data.get(endorsed, {"actblue_url": None, "website_url": None, "facebook_url": None, "twitter_url": None, "instagram_url": None})

with open(r'C:\Users\Robert\Documents\jc-dems-app\candidates.json', 'w') as f:
    json.dump(data, f, indent=2)

total = sum(len(r['candidate_links']) for r in data['races'])
has_actblue = sum(1 for r in data['races'] for lnks in r['candidate_links'].values() if lnks.get('actblue_url'))
has_any = sum(1 for r in data['races'] for lnks in r['candidate_links'].values() if any(lnks.values()))
print(f"Total candidates: {total}, with ActBlue: {has_actblue}, with any link: {has_any}")
