import argparse
from enum import IntEnum
import requests
import urllib.parse
import bs4
import json
import datetime
import csv
import json
import constants
import dateutil
from dateutil import parser
from dateutil import tz
from os import path
import pandas
import pprint
import keys


def ms_to_string(ms:int) -> str:
    td = datetime.timedelta(milliseconds=ms)
    minutes = td.seconds//60
    seconds = td.seconds - minutes*60
    ms = td.microseconds//1000
    minutes_str = str(minutes).rjust(2,'0')
    seconds_str = str(seconds).rjust(2,'0')
    ms_str = str(ms).rjust(3,'0')
    return f"{minutes_str}:{seconds_str}.{ms_str}"

def datetime_to_ms(dt:datetime.datetime) -> int:
    ms = dt.hour*3600000 + dt.minute*60000 + dt.second*1000 + dt.microsecond//1000
    return ms

class Condition(IntEnum):
    DRY = 0
    WET = 1
    ALL = 2

def build_query(host:str, page:int, track:str, condition:int, start_date:datetime.datetime, end_date:datetime.datetime):
    ##https://simracingalliance.emperorservers.com/results?page=0&q=%2BZandvoort+%2BsessionResult.isWetSession%3A1+%2BDate%3A%3E%3D%222022-05-31T02%3A51%3A55Z%22&sort=date
    #"https://simracingalliance.emperorservers.com/results?page=0&q=+zandvoort +sessionResult.isWetSession:1 +Date:>="2022-05-31T02:51:55Z" +Date:<="2022-06-17T02:51:55Z""
    #https://simracingalliance.emperorservers.com/results?page=0&q=%2BZandvoort+%2BsessionResult.isWetSession%3A1+%2BDate%3A%3E%3D%222022-05-31T02%3A51%3A55Z%22+%2BDate%3A%3C%3D%222022-06-17T02%3A51%3A55Z%22&sort=date
    #https://simracingalliance.emperorservers.com/results?page=0&q=%2Bzandvoort+%2BsessionResult.isWetSession%3A1+%2BDate%3A%3E%3D%222022-05-31T02%3A51%3A55Z%22+%2BDate%3A%3C%3D%222022-06-17T02%3A51%3A55Z%22'
    
    start_date_utc = start_date.astimezone(tz=tz.UTC)
    end_date_utc = end_date.astimezone(tz=tz.UTC)
    start_date_str = datetime.datetime.strftime(start_date_utc, "%Y-%m-%dT%H:%M:%SZ")
    end_date_str = datetime.datetime.strftime(end_date_utc, "%Y-%m-%dT%H:%M:%SZ")

    query = f'+{track} +sessionResult.isWetSession:{condition} +Date:>="{start_date_str}" +Date:<="{end_date_str}"'
    query_quote = urllib.parse.quote_plus(query, safe='"')
    return f"https://{host}/results?page={page}&q={query_quote}&sort=date"


class Entry:
    """
    A class representing an entry in a Leaderboard/Session

    Attributes:
        name: Driver name
        id: Driver ID
        car: Car used
        best_time: Best lap time
        s1: Best lap S1
        s2: Best lap S2
        s3: Best lap S3
    """
    def __init__(
            self,
            first_name = "",
            last_name = "",
            short_name = "",
            id:str = "", 
            car:str = "",
            car_raw = 0, 
            best_time:int = None,
            s1:int = None,
            s2:int = None,
            s3:int = None,
            iswet: int = 0
        ) -> None:
        """
        Initialize an Entry

        Args:
            name: Driver name
            id: Driver ID
            car: Car used
            best_time: Best lap time
            s1: Best lap S1
            s2: Best lap S2
            s3: Best lap S3
        """
        self.first_name = first_name
        self.last_name = last_name
        self.short_name = short_name
        self.id = id
        self.car = car
        self.car_raw = car_raw
        self.best_time = best_time
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3
        self.iswet = iswet

    def __str__(self, trail_trim = False) -> str:
        """
        Convert an Entry to a string

        Args:
            suppress_id: Suppress driver ID flag. Enable to prevent printing driver ID
            trail_trim: Trim trailing zeroes of time format. Practically convert microseconds to milliseconds
        Return:
            Formatted string: {Name},{ID},{Car},{Best lap},{Best lap S1},{Best lap S2},{Best lap S3},{IsWet}
        """
        best_time_str = ms_to_string(self.best_time)
        s1_str = ms_to_string(self.s1)
        s2_str = ms_to_string(self.s2)
        s3_str = ms_to_string(self.s3)
        tmp_list = [
            self.first_name,
            self.last_name,
            self.short_name,
            self.id,
            str(self.car),
            str(self.car_raw),
            best_time_str,
            s1_str,
            s2_str,
            s3_str,
            str(self.iswet)
        ]
        tmp_list = [e for e in tmp_list if e is not None]
        return ','.join(tmp_list)

class Session:
    """
    A class representing results of a single session

    Attributes:
        filename: Filename of server results json, i.e 220210_232907_FP
        results: A list of Entries containing the results
    """
    #dash_url = f"https://simracingalliance.emperorservers.com/results"
    #session_res_prefix = f"https://simracingalliance.emperorservers.com/results/"
    #session_json_prefix = f"https://simracingalliance.emperorservers.com/results/download/"
    #simresults_prefix = f"https://simresults.net/remote/csv?result=https%3A%2F%2Fsimracingalliance.emperorservers.com%2Fresults%2Fdownload%2F"
    
    def __init__(self, host:str = None, filename:str = None) -> None:
        """
        Initialize a Session

        Args:
            filename: File name of server results json, i.e 220210_232907_FP
        """
        self.filename = filename
        self.results:list[Entry] = []
        self.dash_url = f"https://{host}/results"
        self.session_res_prefix = f"{self.dash_url}/"
        self.session_json_prefix = f"{self.dash_url}/download/"
        self.track = ""
        self.iswet = 0

    def get_session_results(self):
        """
        Fetch results of a session from Emperor servers and populate the Session instance with that result.
        Ignores sessions with no laps.
        """
        session_json_url = f"{self.session_json_prefix}{self.filename}.json"
        session_json = requests.get(session_json_url, allow_redirects=True).content.decode("utf-8")
        session_json_data = json.loads(session_json)
        self.track = session_json_data['trackName']
        self.iswet = session_json_data['sessionResult']['isWetSession']
        laps = session_json_data['laps']
        if not laps:
            print(f"DB: NO LAPS || {self.session_res_prefix}{self.filename}")
            return

        # Leaderboard lines are cars that were in the session
        # Each car has a list of drivers.
        # An Entry in the Session is made from pair of driver and car and lap times of that pair
        leaderboard_lines = session_json_data['sessionResult']['leaderBoardLines']
        for line in leaderboard_lines:
            car = line['car']
            drivers = car['drivers']
            driver_index = 0
            for driver in drivers:
                entry = Entry()
                car_model = car['carModel']
                entry.car_raw = car_model
                car_id = car['carId']
                if car_model in constants.car_model_dict:
                    entry.car = constants.car_model_dict[car_model]
                else:
                    entry.car = "1996 Toyota Corolla"
                
                driver_name = f"{driver['firstName']} {driver['lastName']} ({driver['shortName']})"
                entry.name = driver_name
                entry.first_name = driver['firstName']
                entry.last_name = driver['lastName']
                entry.short_name = driver['shortName']
                entry.iswet = self.iswet
                
                entry.id = driver['playerId']
                
                min_lap = 3599999 #6 hours max session time (Arbitrary initial minimum)
                min_lap_s1 = 0
                min_lap_s2 = 0
                min_lap_s3 = 0
                valid_lap_set = False
                for lap in laps:
                    if ( (lap['isValidForBest']) and (car_id == lap['carId']) and (driver_index == lap['driverIndex']) ):
                        valid_lap_set = True
                        if (lap['laptime'] <= min_lap):
                            min_lap_s1 = lap['splits'][0]
                            min_lap_s2 = lap['splits'][1]
                            min_lap_s3 = lap['splits'][2]
                            min_lap = lap['laptime']
                entry.best_time = min_lap
                entry.s1 = min_lap_s1
                entry.s2 = min_lap_s2
                entry.s3 = min_lap_s3
                
                if valid_lap_set:
                    self.results.append(entry)
                driver_index += 1

    def __str__(self, suppress_id:bool = False) -> str:
        """
        Convert a Session to a csv string.

        Args:
            suppress_id: Suppress driver ID flag. Enable to prevent printing driver ID
        Return:
            CSV Header: Refer to csv_header in constants.py
            Formatted string: {Name},{ID},{Car},{Best lap},{Best lap S1},{Best lap S2},{Best lap S3}
        """
        results_str = f"{constants.csv_header}\n"
        for entry in self.results:
            results_str += f"{entry.__str__(suppress_id=suppress_id),self.iswet}"
        return results_str

    def to_post_json(self):
        track_dict = {
            "name" : self.track,
            "is_wet": self.iswet
        }
        drivers_list = []
        results_sorted = sorted(self.results, key=lambda e:e.best_time)
        rank = 1
        for entry in results_sorted:
            entry_dict = {
                "rank" : rank,
                "first_name" : entry.first_name,
                "last_name" : entry.last_name,
                "short_name" : entry.short_name,
                "steam_id" : entry.id,
                "car_id" : entry.car_raw,
                "lap_time" : entry.best_time.seconds*1000+entry.best_time.microseconds//1000,
                "sector_1" : entry.s1.seconds*1000+entry.s1.microseconds//1000,
                "sector_2" : entry.s2.seconds*1000+entry.s2.microseconds//1000,
                "sector_3" : entry.s3.seconds*1000+entry.s3.microseconds//1000,
            }
            drivers_list.append(entry_dict)
            rank += 1
        js = {
            "track" : track_dict,
            "drivers" : drivers_list
        }

        return js


class Leaderboard:
    """
    A class representing a leaderboard for a certain track

    Attributes:
        html_dir: Directory of html files
        track: Track
        last_updated: Last updated time
        entry_list: List of Entries
        file_path: Path to csv file
    """
    html_dir = "html"

    def __init__(
        self, track:str = "", 
        last_updated:datetime.datetime = None, 
        entry_list:list[Entry] = None, 
        file_path:str = "", 
        condition:Condition = Condition.ALL, 
        season:int = 3,
        most_recent_sessions = {}
    ) -> None:
        """
        Init the Leaderboard

        Args:
            track: Track
            last_updated: Last updated time
            entry_list: List of Entries
            file_path: Path to csv file
        """
        self.track = track
        self.track_raw = constants.pretty_name_raw_name[self.track]
        self.last_updated = last_updated
        self.entry_list = entry_list
        self.file_path = file_path
        self.condition = condition
        self.season = season
        self.most_recent_sessions = most_recent_sessions

    @classmethod
    def read_leaderboard(cls, track:str, file_path = None):
        """
        Create a new instance populated with csv file contents

        Args:
            file_path: Path to csv
        Return:
            Populated instance of class
        """
        entry_list = []
        last_updated_str = ""
        with open(file_path, "r", encoding='utf-8') as csv_file:
            line_count = 0
            csv_reader = csv.reader(csv_file, delimiter=',')
            most_recent_sessions = {}
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                    continue
                else:
                    if ("Last updated" in row[0]):
                        last_updated_str = row[0].split("?")[1]
                        line_count += 1
                        continue
                    elif ("?MR?" in row[0]):
                        host = row[1]
                        timestamp = row[2]
                        most_recent_sessions[host] = timestamp
                        continue

                    best_time = datetime.datetime.strptime(row[7], "%M:%S.%f")
                    s1 = datetime.datetime.strptime(row[8], "%M:%S.%f")
                    s2 = datetime.datetime.strptime(row[9], "%M:%S.%f")
                    s3 = datetime.datetime.strptime(row[10], "%M:%S.%f")
                    wet = int(row[11])
                    
                    entry = Entry(
                        first_name=row[1],
                        last_name=row[2],
                        short_name=row[3],
                        id=row[4],
                        car=row[5],
                        car_raw=int(row[6]),
                        best_time=datetime_to_ms(best_time),
                        s1=datetime_to_ms(s1),
                        s2=datetime_to_ms(s2),
                        s3=datetime_to_ms(s3),
                        iswet=wet
                    )
                    #print(entry)
                    entry_list.append(entry)
                line_count += 1
        #last_updated = datetime.datetime.strptime(last_updated_str, "%Y-%m-%dT%H:%M:%S%z")
        last_updated = dateutil.parser.parse(last_updated_str)
        return cls(file_path=file_path, entry_list=entry_list, last_updated=last_updated, track=track, most_recent_sessions=most_recent_sessions)

    @classmethod
    def get_leaderboard(cls, season:int, track:str, condition:Condition = Condition.DRY):
        #https://www.simracingalliance.com/api/leaderboard/get/zandvoort/1?season=3
        url = f"https://www.simracingalliance.com/api/leaderboard/get/{constants.pretty_name_raw_name[track]}/{int(condition)}?season={season}"
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'Bearer {keys.SRA_API_KEY}'}
        r = requests.get(url=url, headers=headers)
        c = r.content.decode(encoding='utf-8')
        ldb_dict = json.loads(c)
        if (("error" in ldb_dict) and ldb_dict["error"] == "leaderboard does not exist"):
            print("Leaderboard does not exist. Returning empty leaderboard")
            return cls(track=track, condition=condition, last_updated=datetime.datetime.fromtimestamp(0,tz=tz.UTC), most_recent_sessions=constants.season_starting_session_timestamps[season])

        ldb_data = ldb_dict['data']['leaderboard_data']
        last_updated_str = ldb_dict['data']['leaderboard']['last_updated_iso_8601']
        last_updated = dateutil.parser.parse(last_updated_str).astimezone(tz.UTC)
        most_recent_sessions = ldb_dict['data']['leaderboard']['most_recent_sessions']
        entry_list:list[Entry] = []
        for ldb_entry in ldb_data:
            entry = Entry()
            
            entry.best_time = int(ldb_entry['lap_time'])
            entry.s1 = int(ldb_entry['sector_1'])
            entry.s2 = int(ldb_entry['sector_2'])
            entry.s3 = int(ldb_entry['sector_3'])
            
            driver_dict = ldb_entry['driver']
            entry.first_name = driver_dict['first_name']
            entry.last_name = driver_dict['last_name']
            entry.short_name = driver_dict['short_name']
            entry.id = driver_dict['steam_id']

            car_dict = ldb_entry['car']
            entry.car = f"{car_dict['name']} {car_dict['year']}"
            entry.car_raw = int(car_dict['car_id'])

            entry.iswet = int(condition)

            entry_list.append(entry)

        return cls(entry_list=entry_list, track=track, condition=condition, last_updated=last_updated, season=season, most_recent_sessions=most_recent_sessions)


    def write_leaderboard(self, file_path: None, trail_trim = False):
        """
        Write leaderboard to csv file

        Args:
            file_path: File path
            suppress_id: Suppress driver ID flag
            space_delim: Space delimited mode
            include_timestamp: Include last updated timestamp line flag
            trail_trim: Trim trailing zeroes flag
        """
        if not file_path:
            file_path = self.file_path
        with open(file_path, "w", encoding="utf-8") as file:
            last_updated_str = datetime.datetime.strftime(self.last_updated, "%Y-%m-%dT%H:%M:%S%z")
            file.write(self.__str__(trail_trim=trail_trim))
            file.write(f"Last updated?{last_updated_str}\n")
            for host in constants.host_list:
                file.write(f"?MR?,{host},{self.most_recent_sessions[host]}\n")

    def __str__(self, trail_trim = False) -> str:
        """
        Convert the leaderboard to a csv string

        Args:
            include_timestamp: Include last updated timestamp line flag
            trail_trim: Trim trailing zeroes flag
        Return:
            CSV string
        """

        leaderboard_str = constants.csv_header + "\n"
        rank = 1
        for entry in self.entry_list:
            leaderboard_str += f"{rank},{entry.__str__(trail_trim=trail_trim)}\n"
            rank += 1
        return leaderboard_str

    def update(self, host:str, pages, pw = True, condition:Condition = Condition.ALL) -> bool:
        """
        Update the leaderboard using data fetched from the server

        Args:
            pages: Number of pages to go through. See https://simracingalliance.emperorservers.com/results
            pw: Password restriction flag
        """
        # Flow:
        # Scrape result page html -> Parse result table
        # For each entry get session filename, session html
        # Session html for checking password restriction
        # Pass session filename to Session object and call get_session_results
        # Update leaderboard with Session object

        #https://accsm.simracingalliance.com/results?page=0&q=zandvoort&sort=date

        if not pages:
            pages = 8000

        print(f"HOST: {host}")
        dash_url = f"https://{host}/results"
        session_res_prefix = f"{dash_url}/"
        processed_all_new = False
        most_recent_timestamp:datetime.datetime = None
        ldb_most_recent:datetime.datetime = dateutil.parser.parse(self.most_recent_sessions[host])
        for page in range(0, pages):
            print(f"=====Processing page{page+1}=====")
            dash_query = build_query(
                host=host, 
                page=page, 
                track=self.track_raw, 
                condition=int(self.condition), 
                start_date=constants.season_start_dates[self.season],
                end_date=constants.season_end_dates[self.season]
            )
            dash_request = requests.get(dash_query)
            #dash_request = requests.get(f"{dash_url}?page={page}&q={self.track_raw}&sort=date", allow_redirects=True)
            if (dash_request.status_code == 404):
                print(f"404: {dash_url}?page={page}")
                break
            dash_html = dash_request.content.decode("utf-8")
            soup = bs4.BeautifulSoup(dash_html, "html.parser")
            rows = soup.select(".row-link")

            for row in rows:
                filename = row['data-href'].split('/')[2]
                #track_excludes = constants.session_exclude[self.track]
                if ((self.track in constants.session_exclude) and (filename in constants.session_exclude[self.track])):
                    print(f"DB: Excluded session || {session_res_prefix}{filename}")
                    continue
                session_res_url = f"{session_res_prefix}{filename}"
                session_res_html = requests.get(session_res_url, allow_redirects=True).content.decode("utf-8")
                if (
                    pw and
                    ("Password: sra" not in session_res_html) and 
                    ("SRA League race" not in session_res_html)
                ):
                    print(f"DB: No password || {session_res_prefix}{filename}")
                    continue
                print(f"Processing: {session_res_prefix}{filename}")
                children = row.contents
                timestamp_str = children[1].contents[0].strip()
                session_type = children[3]
                track = children[5].contents[0].strip()
                #timestamp = datetime.datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S %Z")
                timestamp = dateutil.parser.parse(timestamp_str)
                delta = timestamp - self.last_updated
                updated = False
                if not most_recent_timestamp:
                    most_recent_timestamp = timestamp

                if ( (track == self.track) and ((pages != 8000) or (timestamp >= ldb_most_recent)) ):   #If track matches and new
                    updated = True
                    session = Session(host, filename)
                    session.get_session_results()
                    self.track_raw = session.track
                    if not session.results:
                        continue
                    if (condition != Condition.ALL):
                        if (self.condition != session.iswet):
                            print(f"DB: Condition doesn't match || {session_res_prefix}{filename}")
                            continue
                    if not self.entry_list:
                        self.entry_list = session.results
                        continue
                    for session_entry in session.results:
                        found_flag = False
                        for leaderboard_entry in self.entry_list:
                            # If car and ID match
                            if ( (leaderboard_entry.id == session_entry.id) and (leaderboard_entry.car_raw == session_entry.car_raw) ):
                                found_flag = True
                                if (leaderboard_entry.best_time > session_entry.best_time):
                                    leaderboard_entry.best_time = session_entry.best_time
                                    leaderboard_entry.s1 = session_entry.s1
                                    leaderboard_entry.s2 = session_entry.s2
                                    leaderboard_entry.s3 = session_entry.s3
                        
                        #If session entry is not in leaderboard entry
                        if not found_flag:
                            self.entry_list.append(session_entry)
                else:
                    if (track != self.track):
                        print(f"DB: Track doesn't match || {session_res_prefix}{filename}")
                    elif (timestamp <= ldb_most_recent):
                        print(f"DB: Old session || {session_res_prefix}{filename}")
                        if (pages==8000):
                            print("Processed all new sessions. Stopping...")
                            processed_all_new = True
                            break
                    else:
                        print(f"DB: Unknown error || {session_res_prefix}{filename}")
            print(f"=====Finished page{page+1}=====")
            if processed_all_new:
                break
        if (ldb_most_recent <= most_recent_timestamp):
            ldb_most_recent = most_recent_timestamp
            self.most_recent_sessions[host] = datetime.datetime.strftime(most_recent_timestamp, "%Y-%m-%dT%H:%M:%SZ")
        else:
            print("Server most recent is older than leaderboard most recent. Aborting")
            print(f"{self.most_recent_sessions[host]} > {most_recent_timestamp}")
            return False
        print("#######################################################")
        if (self.entry_list):
            self.entry_list.sort(key=lambda x: x.best_time)
        return updated

    def get_html_dir_path(self):
        return path.join(self.html_dir, f"{self.track}")
    def get_html_path(self):
        return path.join(self.get_html_dir_path(), f"{self.track}.html")
    def get_html_csv_path(self):
        return path.join(self.get_html_dir_path(), f"{self.track}.csv")
    def get_css_path(self):
        return path.join(self.get_html_dir_path(), f"external.css")

    def to_html(self, suppress_id=True, include_timestamp=False, trail_trim=True):
        html_path = self.get_html_path()
        html_csv_path = self.get_html_csv_path()
        css_path = self.get_css_path()
        if not path.exists(css_path):
            with open(css_path, "w") as css_file:
                css_file.write(constants.css_string)
        self.write_leaderboard(file_path=html_csv_path, suppress_id=suppress_id, include_timestamp=include_timestamp, trail_trim=trail_trim)
        pandas_csv = pandas.read_csv(html_csv_path, encoding='utf-8')
        pandas_html = pandas_csv.to_html(None, index=False, justify='center', classes="ldb-table")
        with open(html_path, "w", encoding="utf-8") as html_file:
            html_file.write(constants.html_string.format(ldb_html=pandas_html))
        return

    def to_post_json(self):
        track_dict = {
            "name" : self.track_raw,
            "is_wet": int(self.condition),
            "most_recent_sessions" : self.most_recent_sessions
        }
        drivers_list = []
        entries_sorted = sorted(self.entry_list, key=lambda e:e.best_time)
        rank = 1
        for entry in entries_sorted:
            entry_dict = {
                "rank" : rank,
                "first_name" : entry.first_name,
                "last_name" : entry.last_name,
                "short_name" : entry.short_name,
                "steam_id" : entry.id,
                "car_id" : entry.car_raw,
                "lap_time" : entry.best_time,
                "sector_1" : entry.s1,
                "sector_2" : entry.s2,
                "sector_3" : entry.s3,
            }
            drivers_list.append(entry_dict)
            rank += 1
        js = {
            "track" : track_dict,
            "drivers" : drivers_list
        }

        return js

    def post_leaderboard(self):
        js = self.to_post_json()
        url = "https://www.simracingalliance.com/api/leaderboard/update"
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'Bearer {keys.SRA_API_KEY}'}
        r = requests.post(url, data=json.dumps(js), headers=headers)
        return r
    
    def finalize(self):
        self.last_updated = datetime.datetime.now(datetime.timezone.utc)


def main(track:str, condition:int, season:int = 3, pages:int = None, simulate:bool = False):
    leaderboard = Leaderboard.get_leaderboard(season=season, track=constants.pretty_name_raw_name[track], condition=condition)
    for host in constants.host_list:
        leaderboard.update(host=host, pages=pages, pw=True, condition=condition)
    leaderboard.finalize()
    if simulate:
        leaderboard.write_leaderboard(f"{track}_POST.csv", True)
    else:
        r = leaderboard.post_leaderboard()
        print(r)
    return 0

def __main(track:str, condition:int, season:int = 3, pages:int = None, simulate:bool = False):
    #print(ms_to_string(33235))
    leaderboard = Leaderboard.get_leaderboard(season=season, track=constants.pretty_name_raw_name[track], condition=condition)
    #leaderboard.update(host=constants.host_list[0], pages=pages, pw=False, condition=condition)
    #leaderboard = Leaderboard.get_leaderboard(season=3, track="Zandvoort", condition=Condition.WET)
    #leaderboard = Leaderboard.read_leaderboard("Donington", "donington_POST.csv")
    #leaderboard.track = "Donington"
    leaderboard.condition = Condition.DRY
    leaderboard.update(constants.host_list[0], pages=pages, pw=False, condition=Condition.DRY)
    leaderboard.update(host=constants.host_list[1], pages=pages, pw=False, condition=Condition.DRY)
    leaderboard.write_leaderboard("Donington.csv", True)
    js = leaderboard.to_post_json()
    pp = pprint.PrettyPrinter(indent=4, sort_dicts=False, compact=False)
    pp.pprint(js)
    #r = leaderboard.post_leaderboard()
    #print(r)

    #print(build_query(constants.host_list[0], 0, track, condition, constants.season_start_dates[season], constants.season_end_dates[season]))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("track", type=str, choices=constants.track_choices, help="Track to update")
    parser.add_argument("condition", type=int, choices=[0,1], help="Track condition. 0 for dry. 1 for wet")
    parser.add_argument("season", type=int, nargs='?', choices=[1,2,3], default=3, help="Leaderboard season")
    parser.add_argument('--pages', type=int, help="Override amount of pages. Stop upon 404")
    parser.add_argument('--simulate', action='store_true', help="Simulation mode. Writes updated leaderboard to a file")

    #args = parser.parse_args("brands_hatch 0 --pages 7".split(' '))
    args = parser.parse_args()
    print(args)
    main(track=args.track, condition=args.condition, pages=args.pages, simulate=args.simulate)
