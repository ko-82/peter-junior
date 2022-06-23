from datetime import datetime
from dateutil import parser
from dateutil import tz
from collections import namedtuple

TEST_CHANNEL_ID=920858193624694874
CONTROL_CHANNEL_ID=929202593882837022
SRA_GUILD_ID=915686674833498203
SRA_ADMIN_ROLE_ID=915687122608988181
SRA_TECH_ROLE_ID=941515168960098455
SRA_ACCEPT_EMOJI_ID=987218470036983838


ST_U_H_ENTRY = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**\n\
- 1mm lower front ride height\n\
- 1 click lower rear wing\n\
- 2mm higher rear height\n\
- 1 click higher front bumpstop range\n\
- 1 click lower front bumpstop rate\n\
- Less front braking balance\n\
- Less preload\n\
Generic:\n\
- More front negative camber\n\
- Less rear negative camber\n\
- Less rear toe\n\
"
ST_U_H_MID = ST_U_H_ENTRY
ST_U_H_EXIT = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**\n\
From more to less influence.\n\
- 1mm lower front ride height\n\
- 1 click lower rear wing\n\
- 2mm higher rear height\n\
- Lower rear bumpstop range to 15 and then lower slowly from there and check results \n\
(Advice to keep rear bumpstop rate as low as possible.)\n\
- 1 click higher front bumpstop range\n\
- 1 click lower front bumpstop rate\n\
- Less Traction Control\n\
- Less preload\n\
Generic:\n\
- More front negative camber\n\
- Less rear negative camber\n\
- Less rear toe\n\
"

ST_U_L_ENTRY = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**\n\
From more to less influence.\n\
- Less front braking balance\n\
- 1 click higher front bumpstop range\n\
- 1 click lower front bumpstop rate\n\
- 1 click lower front wheel rate\n\
- 1 click lower front antiroll bar\n\
- 1mm lower front ride height\n\
- 2mm higher rear height\n\
- Less preload\n\
Generic:\n\
- More front negative camber\n\
- Less rear negative camber\n\
- Less rear toe\n\
"

ST_U_L_MID = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**.\n\
From more to less influence.\n\
- 1 click higher front bumpstop range\n\
- 1 click lower front bumpstop rate\n\
- 1 click lower front wheel rate\n\
- 1 click lower front antiroll bar\n\
- 1mm lower front ride height\n\
- 2mm higher rear height\n\
- Less preload\n\
Generic:\n\
- More front negative camber\n\
- Less rear negative camber\n\
- Less rear toe\n\
"

ST_U_L_EXIT = "\
Assuming pressures are correct.\n\
**Do only one modification at a time.\n\
From more to less influence.\n\
- 1 click higher front bumpstop range\n\
- 1 click lower front bumpstop rate\n\
- 1 click lower front wheel rate\n\
- 1 click lower front antiroll bar\n\
- 1mm lower front ride height\n\
- 2mm higher rear height\n\
- Less preload\n\
Generic:\n\
- More front negative camber\n\
- Less rear negative camber\n\
- Less rear toe\n\
"

ST_O_H_ENTRY = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**\n\
From more to less influence.\n\
- 1 click higher rear wing\n\
- 1mm higher front ride height\n\
- 2mm lower rear height\n\
- 1 click lower front bumpstop range\n\
- 1 click higher front bumpstop rate\n\
- More front braking balance\n\
- More preload\n\
Generic:\n\
- Less front negative camber\n\
- More rear negative camber\n\
- More rear toe\n\
"

ST_O_H_MID = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**\n\
From more to less influence.\n\
- 1 click higher rear wing\n\
- 1mm higher front ride height\n\
- 2mm lower rear height\n\
- 1 click lower front bumpstop range\n\
- 1 click higher front bumpstop rate\n\
- More preload\n\
Generic:\n\
- Less front negative camber\n\
- More rear negative camber\n\
- More rear toe\n\
"

ST_O_H_EXIT = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**\n\
From more to less influence. \n\
- 1 click higher rear wing\n\
- 2mm lower rear height\n\
- 1mm higher front ride height\n\
- 1 click lower front bumpstop range\n\
- 1 click higher front bumpstop rate\n\
Generic:\n\
- Less front negative camber\n\
- More rear toe\n\
"

ST_O_L_ENTRY = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**\n\
From more to less influence. \n\
- More front braking balance\n\
- 1 click lower front bumpstop range\n\
- 1 click higher front bumpstop rate\n\
- 1 click higher front wheel rate\n\
- 2mm lower rear height\n\
- 1 click higher front antiroll bar\n\
- 1mm higher front ride height\n\
- More preload\n\
Generic:\n\
- Less front negative camber\n\
- More rear negative camber\n\
- More rear toe\n\
"

ST_O_L_MID = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**\n\
From more to less influence.\n\
- 1 click higher front wheel rate\n\
- 2mm lower rear height\n\
- 1 click higher front antiroll bar\n\
- 1mm higher front ride height\n\
- 1 click lower front bumpstop range\n\
- 1 click higher front bumpstop rate\n\
- More preload\n\
Generic:\n\
- Less front negative camber\n\
- More rear negative camber\n\
- More rear toe\n\
"

ST_O_L_EXIT = "\
Assuming pressures are correct.\n\
**Do only one modification at a time**\n\
From more to less influence. \n\
- Higher TC level\n\
- Max rear bumpstop range (avoid touching the bumpstops under acceleration)\n\
- 2mm lower rear height\n\
- 1 click higher front wheel rate\n\
- 1 click higher front antiroll bar\n\
- 1mm higher front ride height\n\
- 1 click lower front bumpstop range\n\
- 1 click higher front bumpstop rate\n\
- Less preload\n\
Generic:\n\
- Less front negative camber\n\
- More rear toe\n\
"

ST_K = "\
Assuming pressures are correct.\n\
Do only one modification at a time\n\
From more to less influence. \n\
- 2 click higher front bumpstop range\n\
- 2 click lower front bumpstop rate\n\
- 1 click lower front antiroll bar\n\
- 1 click lower rear antiroll bar\n\
- Adjust fast bump and rebound dampers.\n\
There is no easy way to give a rule of thumb.\n\
Normally you should use a soft fast bump and a bit higher fast rebound. But if your suspension is stiff, you might see that the lower you go the worse it gets. If that’s the case you need to raise fast bump to a much higher value(stiffer) and then fine tune again.\n\
This happens because you need to control how much energy the spring absorbs from hitting a kerb (bump). All this energy needs to be released (rebound). If your damper is too soft, it will permit the spring to accumulate too much energy and you won’t be able to control it (jump).\n\
Also… because dampers are magic.\n\
"

ST_U2O_H = "\
When the car changes from under to oversteer on mid to high-speed pedal work, try the following:\n\
Assuming pressures are correct.\n\
Do only one modification at a time\n\
From more to less influence. \n\
- 1 clicks stiffer (higher numbers) wheel rates all around\n\
- 1 click lower front bumpstop range\n\
- 2 clicks stiffer slow dampers all around\n\
- 1 click higher rear wing\n\
"

ST_U2O_L = "\
When the car changes from under to oversteer on mid to low-speed pedal work, try the following:\n\
Assuming pressures are correct.\n\
Do only one modification at a time\n\
From more to less influence. \n\
- 1 click stiffer (higher numbers) front wheel rates\n\
- 1 clicks softer (lower numebrs) slow dampers all around\n\
- 2mm lower rear ride height\n\
"

ST_PR = "\
Here are the ideal tyre pressures range.\n\
All GT3 dry slicks: 27.4-28.0 psi \n\
All GT3 wet tyres: 29.5-30.5 psi\n\
All GT4 dry slicks: 26.5-27.5 psi\n\
All GT4 wet tyres: 29.5-30.5 psi\n\
Obviously depending on the situations and conditions you might find better handling and performance even if you go outside the proposed pressure ranges, but it is a good idea to stay in between initially.\n\
"

ST_TMP_H = "\
Assuming pressures are correct.\n\
Do only one modification at a time\n\
From more to less influence.\n\
- Driving style is the most important factor\n\
- Open brake ducts (higher numbers)\n\
- Less negative camber\n\
- Less toe\n\
- 2 clicks softer fast dampers\n\
- 2 clicks softer slow dampers\n\
- Higher ABS and TC levels\n\
"

ST_TMP_L = "\
Assuming pressures are correct.\n\
Do only one modification at a time\n\
From more to less influence. \n\
- Close brake ducts (lower numbers)\n\
- More negative camber\n\
- More toe\n\
- 2 clicks stiffer fast dampers\n\
- 2 clicks stiffer slow dampers\n\
- Lower ABS and TC levels\n\
"

ST_BRK = "\
Brake pads and brake discs wear is relative to the brake pad choice, temperatures, driving style, ABS and brake bias usage. Brake disc and pad wear is shown at the end of each driving session, when you return to your strategy setup UI on the 'last readings' box.\n\
Additionally, brake pads consumption will appear as a red dot in the center of the brake discs heat visualization in the tyre and brakes HUD, when brake pads are under 10mm thickness.\n\
\n\
Pad 1: Very aggressive friction coefficient, max braking performance, aggressive disc and pad wear. Pedal modulation can be tricky if out of temperature or as it wears down. Use in hotlap and qualifying sessions, sprint races and can withstand 3 hours races. Risky and dangerous to use over 3 or 4 hours because the pads will wear down, overheat and lose linearity in brake pedal feel.\n\
Pad 2: Very Good friction coefficient, very good braking performance, good disc and pad wear. Pedal modulation almost always good and linear, good feedback while overheating and gradual wear. Perfect for endurance racing, but can also be used in hotlap , qualifying sessions as well as sprint races as what it loses in performance, regains in braking modulation and predictability. The default choice for long endurance races, easily makes 12 hours and can make 24 hours race too with a bit of care. Will also overheat and lose linearity in brake pedal feel when worn out, but in a more predictable way and after much longer stints. Because of the lower friction, you could possibly use smaller brake ducts.\n\
Pad 3: Moderate friction coefficient, braking zones can be longer in dry, very moderate disc and pad wear. Excellent pedal modulation also in cold ambient conditions, very linear pedal feedback. Excellent choice for wet conditions and very long endurance races. Very predictable and easy to modulate brake pad.\n\
Pad 4: Identical to pad1 but with exaggerated wear for fade demonstration purposes.\n\
"

ST_HELP = '\
Hello, I can try to help you with some basic advice, but please always remember that the problem is between the steering wheel and the racing seat...\n\
\n\
Please specify the issue by typing at the #setup-bot channel:\n\
$$setup --help\n\
\n\
$$setup "understeer high speed entry"\n\
$$setup "understeer high speed apex"\n\
$$setup "understeer high speed exit"\n\
$$setup "understeer low speed entry"\n\
$$setup "understeer low speed apex"\n\
$$setup "understeer low speed exit"\n\
\n\
$$setup "oversteer high speed entry"\n\
$$setup "oversteer high speed apex"\n\
$$setup "oversteer high speed exit"\n\
$$setup "oversteer low speed entry"\n\
$$setup "oversteer low speed apex"\n\
$$setup "oversteer low speed exit"\n\
\n\
$$setup "car bounces on kerbs/bumps"\n\
$$setup "high speed over/under"\n\
$$setup "low speed over/under"\n\
\n\
$$setup "tyre pressures"\n\
$$setup "tyres overheating"\n\
$$setup "tyres cold"\n\
$$setup "brake pads"\n\
'

setup_dict = {
    '--help': ST_HELP,
    'understeer high speed entry': ST_U_H_ENTRY,
    'understeer high speed apex': ST_U_H_MID,
    'understeer high speed exit': ST_U_H_EXIT,
    'understeer low speed entry': ST_U_L_ENTRY,
    'understeer low speed apex': ST_U_L_MID,
    'understeer low speed exit': ST_U_L_EXIT,
    'oversteer high speed entry': ST_O_H_ENTRY,
    'oversteer high speed apex': ST_O_H_MID,
    'oversteer high speed exit': ST_O_H_EXIT,
    'oversteer low speed entry': ST_O_L_ENTRY,
    'oversteer low speed apex': ST_O_L_MID,
    'oversteer low speed exit': ST_O_L_EXIT,
    'car bounces on kerbs/bumps': ST_K,
    'high speed over/under': ST_U2O_H,
    'low speed over/under': ST_U2O_L,
    'tyre pressures': ST_PR,
    'tyres overheating': ST_TMP_H,
    'tyres cold': ST_TMP_L,
    'brake pads': ST_BRK,
}

car_model_dict = {
    0 : 'Porsche 991 GT3',
    1 : 'Mercedes AMG GT3',
    2 : 'Ferrari 488 GT3',
    3 : 'Audi R8 GT3 2015',
    4 : 'Lamborghini Huracan GT3',
    5 : 'McLaren 650s GT3',
    6 : 'Nissan GT-R Nismo GT3 2018',
    7 : 'BMW M6 GT3',
    8 : 'Bentley Continental GT3 2018',
    9 : 'Porsche 991 II GT3 Cup',
    10 : 'Nissan GT-R Nismo GT3 2015',
    11 : 'Bentley Continental GT3 2015',
    12 : 'Aston Martin Vantage V12 GT3',
    13 : 'Lamborghini Gallardo R-EX',
    14 : 'Emil Frey Jaguar G3',
    15 : 'Lexus RC F GT3',
    16 : 'Lamborghini Huracan Evo 2019',
    17 : 'Honda NSX GT3',
    18 : 'Lamborghini Huracan SuperTrofeo',
    19 : 'Audi R8 LMS Evo 2019',
    20 : 'Aston Martin Vantage V8 2019',
    21 : 'Honda NSX Evo 2019',
    22 : 'McLaren 720S GT3 Special',
    23 : 'Porsche 991 II GT3 R 2019',
    24 : 'Ferrari 488 GT3 Evo',
    25 : 'Mercedes AMG GT3 2020',
    30 : 'BMW M4 GT3 2022',
    31 : 'Audi R8 LMS Evo II 2022',
    50 : 'Alpine A110 GT4',
    51 : 'Aston Martin Vantage GT4',
    52 : 'Audi R8 LMS GT4',
    53 : 'BMW M4 GT4',
    54 : 'NaN',
    55 : 'Chevrolet Camaro GT4',
    56 : 'Ginetta G55 GT4',
    57 : 'KTM X-Bow GT4',
    58 : 'Maserati MC GT4',
    59 : 'McLaren 570S GT4',
    60 : 'Mercedes AMG GT4',
    61 : 'Porsche 718 Cayman GT4'
}

#csv_header = f"Rank,Driver,ID,Car,Lap Time,Sector 1,Sector 2,Sector 3,Wet"
csv_header = f"Rank,First Name, Last Name, Short Name,ID,Car,Car Model,Lap Time,Sector 1,Sector 2,Sector 3,Wet"
csv_header_no_id = f"Rank,Driver,Car,Lap Time,Sector 1,Sector 2,Sector 3,Wet"

html_string = """
<html>
  <head><title>HTML Pandas Dataframe with CSS</title></head>
  <link rel="stylesheet" type="text/css" href="../external.css"/>
  <body>
    {ldb_html}
  </body>
</html>
"""

css_string = """
.ldb-table
{
    background-color: #202124;
    color: white;
    font-family: sans-serif;
    font-size: 20px;
    width: 100%;
}

tr:nth-child(even)
{
    background-color: #3b3b3b;
}

td
{
    padding-top: 5px;
    padding-bottom: 5px;
    padding-right: 5px;
    padding-left: 5px;
}

body
{
    background-color: #202124;
}

"""

host_list = ["simracingalliance.emperorservers.com", "accsm.simracingalliance.com"]

session_exclude = {
    "Silverstone": ['220203_033813_FP', '220203_043850_FP', '220207_002120_FP', '220206_194749_FP'],
    "Imola": [],
    "Spa": [],
    "Suzuka": [],
    "Oulton Park": [],
    "Monza": [],
    "Paul Ricard": []
}

ErrorCode = namedtuple("ErrorCode", "code message")
LeaderboardParams = namedtuple("LeaderboardParams", "track condition season")

track_choices = [
    "barcelona",
    "brands_hatch",
    "donington",
    "hungaroring",
    "imola",
    "kyalami",
    "laguna_seca",
    "misano",
    "monza",
    "mount_panorama",
    "nurburgring",
    "oulton_park",
    "paul_ricard",
    "silverstone",
    "snetterton",
    "spa",
    "suzuka",
    "zolder",
    "zandvoort"
]

pretty_name_raw_name = {
    "Barcelona" : "barcelona",
    "Brands Hatch" : "brands_hatch",
    "Donington" : "donington",
    "Hungaroring" : "hungaroring",
    "Imola" : "imola",
    "Kyalami" : "kyalami",
    "Laguna Seca" : "laguna_seca",
    "Misano" : "misano",
    "Monza" : "monza",
    "Mount Panorama" : "mount_panorama",
    "Nurburgring" : "nurburgring",
    "Oulton Park" : "oulton_park",
    "Paul Ricard" : "paul_ricard",
    "Silverstone" : "silverstone",
    "Snetterton" : "snetterton",
    "Spa" : "spa",
    "Suzuka" : "suzuka",
    "Zolder" : "zolder",
    "Zandvoort" : "zandvoort",
    "barcelona" : "Barcelona",
    "brands_hatch" : "Brands Hatch",
    "donington" : "Donington",
    "hungaroring" : "Hungaroring",
    "imola" : "Imola",
    "kyalami" : "Kyalami",
    "laguna_seca" : "Laguna Seca",
    "misano" : "Misano",
    "monza" : "Monza",
    "mount_panorama" : "Mount Panorama",
    "nurburgring" : "Nurburgring",
    "oulton_park" : "Oulton Park",
    "paul_ricard" : "Paul Ricard",
    "silverstone" : "Silverstone",
    "snetterton" : "Snetterton",
    "spa" : "Spa",
    "suzuka" : "Suzuka",
    "zolder" : "Zolder",
    "zandvoort" : "Zandvoort",
}

season_start_dates = {
    1 : parser.isoparse("2022-01-25T00:00:00+0000"),
    2 : parser.isoparse("2022-03-22T00:00:00+0000"),
    3 : parser.isoparse("2022-05-31T00:00:00+0000")
}

season_end_dates = {
    1 : parser.isoparse("2022-03-22T00:00:00+0000"),
    2 : parser.isoparse("2022-05-31T00:00:00+0000"),
    3 : parser.isoparse("2040-05-31T00:00:00+0000")
}

season_starting_session_timestamps = {
    1: {
        "simracingalliance.emperorservers.com" : season_start_dates[1],
        "accsm.simracingalliance.com" : season_start_dates[1]
    },
    2: {
        "simracingalliance.emperorservers.com" : season_start_dates[2],
        "accsm.simracingalliance.com" : season_start_dates[2]
    },
    3: {
        "simracingalliance.emperorservers.com" : season_start_dates[3],
        "accsm.simracingalliance.com" : season_start_dates[3]
    },
}

#https://simracingalliance.emperorservers.com/results?page=0&q=%2BZandvoort+%2BsessionResult.isWetSession%3A1+%2BDate%3A%3E%3D%222022-05-31T02%3A51%3A55Z%22&sort=date