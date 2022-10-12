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

host_list = ["accsm1.simracingalliance.com", "accsm2.simracingalliance.com", "accsm3.simracingalliance.com"]

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
LeaderboardParams = namedtuple("LeaderboardParams", "track_set track condition season")
#TrackParams = namedtuple("TrackParams", "name condition season")

track_choices = [
    "barcelona",
    "brands_hatch",
    "cota",
    "donington",
    "hungaroring",
    "imola",
    "indianapolis",
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
    "watkins_glen",
    "zolder",
    "zandvoort"
]

pretty_name_raw_name = {
    "Barcelona" : "barcelona",
    "Brands Hatch" : "brands_hatch",
    "Cota" : "cota",
    "Donington" : "donington",
    "Hungaroring" : "hungaroring",
    "Imola" : "imola",
    "Indianapolis": "indianapolis",
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
    "Watkins Glen" : "watkins_glen",
    "Zolder" : "zolder",
    "Zandvoort" : "zandvoort",
    "barcelona" : "Barcelona",
    "brands_hatch" : "Brands Hatch",
    "cota" : "Cota",
    "donington" : "Donington",
    "hungaroring" : "Hungaroring",
    "imola" : "Imola",
    "indianapolis": "Indianapolis",
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
    "watkins_glen" : "Watkins Glen",
    "zolder" : "Zolder",
    "zandvoort" : "Zandvoort",
}

discord_track_choices = {
    "Barcelona" : "barcelona",
    "Brands Hatch" : "brands_hatch",
    "Cota" : "cota",
    "Donington" : "donington",
    "Hungaroring" : "hungaroring",
    "Imola" : "imola",
    "Indianapolis": "indianapolis",
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
    "Watkins Glen" : "watkins_glen",
    "Zolder" : "zolder",
    "Zandvoort" : "zandvoort",
}

season_start_dates = {
    1 : parser.isoparse("2022-01-25T00:00:00+0000"),
    2 : parser.isoparse("2022-03-22T00:00:00+0000"),
    3 : parser.isoparse("2022-05-31T00:00:00+0000"),
    4 : parser.isoparse("2022-08-01T00:00:00+0000")
}

season_end_dates = {
    1 : parser.isoparse("2022-03-22T00:00:00+0000"),
    2 : parser.isoparse("2022-05-31T00:00:00+0000"),
    3 : parser.isoparse("2022-07-31T00:00:00+0000"),
    4 : parser.isoparse("2040-05-31T00:00:00+0000")
}

season_starting_session_timestamps = {
    1: {
        "simracingalliance.emperorservers.com" : "2022-01-25T00:00:00+0000",
        "accsm.simracingalliance.com" : "2022-01-25T00:00:00+0000",
        "accsm1.simracingalliance.com" : "2022-01-25T00:00:00+0000"
    },
    2: {
        "simracingalliance.emperorservers.com" : "2022-03-22T00:00:00+0000",
        "accsm.simracingalliance.com" : "2022-03-22T00:00:00+0000",
        "accsm1.simracingalliance.com" : "2022-03-22T00:00:00+0000"
    },
    3: {
        "simracingalliance.emperorservers.com" : "2022-05-31T00:00:00+0000",
        "accsm.simracingalliance.com" : "2022-05-31T00:00:00+0000",
        "accsm1.simracingalliance.com" : "2022-05-31T00:00:00+0000"
    },
    4: {
        "simracingalliance.emperorservers.com" : "2022-08-01T00:00:00+0000",
        "accsm.simracingalliance.com" : "2022-08-01T00:00:00+0000",
        "accsm1.simracingalliance.com" : "2022-08-01T00:00:00+0000",
        "accsm2.simracingalliance.com" : "2022-08-01T00:00:00+0000",
        "accsm3.simracingalliance.com" : "2022-08-01T00:00:00+0000"
    },
}

#https://simracingalliance.emperorservers.com/results?page=0&q=%2BZandvoort+%2BsessionResult.isWetSession%3A1+%2BDate%3A%3E%3D%222022-05-31T02%3A51%3A55Z%22&sort=date