from collections import namedtuple
import requests
import bs4
import json
import datetime
import time
import csv
import json
import re
import constants
from dateutil import parser
from os import path
import pandas


def laptimetostring(td: datetime.timedelta, trail_trim = False) -> str:
    """
    Convert ACC laptime (a timedelta object) to string
    
    Args:
        td: timedelta object
        trail_trim: trim trailing zeroes (practically converts us to ms)
    Return:
        String in MM:ss.SSS format or MM:ss.SSSSSS format
    """
    minutes = td.seconds//60
    seconds = td.seconds - minutes*60
    subsecond = td.microseconds
    just_mod = 0
    if trail_trim:
        subsecond = subsecond//1000
        just_mod = 3
    return f"{str(minutes).rjust(2,'0')}:{str(seconds).rjust(2,'0')}.{str(subsecond).rjust(6-just_mod,'0')}"

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
            self, name:str = "", 
            id:str = "", 
            car:str = "", 
            best_time:datetime.timedelta = None, 
            s1:datetime.timedelta = None,
            s2:datetime.timedelta = None,
            s3:datetime.timedelta = None
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
        self.name = name
        #self.abbr = re.match(r".*\((.+)\)", name).group(1)
        self.id = id
        self.car = car
        self.best_time = best_time
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3

    def __str__(self, suppress_id:bool = False, trail_trim = False) -> str:
        """
        Convert an Entry to a string

        Args:
            suppress_id: Suppress driver ID flag. Enable to prevent printing driver ID
            trail_trim: Trim trailing zeroes of time format. Practically convert microseconds to milliseconds
        Return:
            Formatted string: {Name},{ID},{Car},{Best lap},{Best lap S1},{Best lap S2},{Best lap S3}
        """
        best_time_str = laptimetostring(self.best_time, trail_trim)
        s1_str = laptimetostring(self.s1, trail_trim)
        s2_str = laptimetostring(self.s2, trail_trim)
        s3_str = laptimetostring(self.s3, trail_trim)
        if not suppress_id:
            return f"{self.name},{self.id},{self.car},{best_time_str},{s1_str},{s2_str},{s3_str}"
        return f"{self.name},{self.car},{best_time_str},{s1_str},{s2_str},{s3_str}"

class Session:
    """
    A class representing results of a single session

    Attributes:
        filename: Filename of server results json, i.e 220210_232907_FP
        results: A list of Entries containing the results
    """
    dash_url = f"https://simracingalliance.emperorservers.com/results"
    session_res_prefix = f"https://simracingalliance.emperorservers.com/results/"
    session_json_prefix = f"https://simracingalliance.emperorservers.com/results/download/"
    simresults_prefix = f"https://simresults.net/remote/csv?result=https%3A%2F%2Fsimracingalliance.emperorservers.com%2Fresults%2Fdownload%2F"
    
    def __init__(self, filename:str = None) -> None:
        """
        Initialize a Session

        Args:
            filename: File name of server results json, i.e 220210_232907_FP
        """
        self.filename = filename
        self.results:list[Entry] = []

    def get_session_results(self):
        """
        Fetch results of a session from Emperor servers and populate the Session instance with that result.
        Ignores sessions with no laps.
        """
        session_json_url = f"{Session.session_json_prefix}{self.filename}.json"
        session_json = requests.get(session_json_url, allow_redirects=True).content.decode("utf-8")
        session_json_data = json.loads(session_json)
        laps = session_json_data['laps']
        if not laps:
            print(f"DB: NO LAPS || {Session.session_res_prefix}{self.filename}")
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
                car_id = car['carId']
                if car_model in constants.car_model_dict:
                    entry.car = constants.car_model_dict[car_model]
                else:
                    entry.car = "1996 Toyota Corolla"
                
                driver_name = f"{driver['firstName']} {driver['lastName']} ({driver['shortName']})"
                entry.name = driver_name
                
                entry.id = driver['playerId']
                
                min_lap = 3599999 #6 hours max session time (Arbitrary initial minimum)
                min_lap_s1 = 0
                min_lap_s2 = 0
                min_lap_s3 = 0
                for lap in laps:
                    if ( (lap['isValidForBest']) and (car_id == lap['carId']) and (driver_index == lap['driverIndex']) ):
                        if (lap['laptime'] <= min_lap):
                            min_lap_s1 = lap['splits'][0]
                            min_lap_s2 = lap['splits'][1]
                            min_lap_s3 = lap['splits'][2]
                            min_lap = lap['laptime']
                entry.best_time = datetime.timedelta(milliseconds=min_lap)
                entry.s1 = datetime.timedelta(milliseconds=min_lap_s1)
                entry.s2 = datetime.timedelta(milliseconds=min_lap_s2)
                entry.s3 = datetime.timedelta(milliseconds=min_lap_s3)
                
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
            results_str += f"{entry.__str__(suppress_id=suppress_id)}"
        return results_str


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

    def __init__(self, track:str = "", last_updated:datetime.datetime = None, entry_list:list[Entry] = None, file_path:str = "") -> None:
        """
        Init the Leaderboard

        Args:
            track: Track
            last_updated: Last updated time
            entry_list: List of Entries
            file_path: Path to csv file
        """
        self.track = track
        self.last_updated = last_updated
        self.entry_list = entry_list
        self.file_path = file_path

    @classmethod
    def read_leaderboard(cls, file_path = None):
        """
        Create a new instance populated with csv file contents

        Args:
            file_path: Path to csv
        Return:
            Populated instance of class
        """
        entry_list = []
        last_updated_str = ""
        with open(file_path, "r") as csv_file:
            line_count = 0
            csv_reader = csv.reader(csv_file, delimiter=',')
            for row in csv_reader:
                if line_count == 0:
                    line_count += 1
                    continue
                else:
                    if ("Last updated" in row[0]):
                        last_updated_str = row[0].split("?")[1]
                        line_count += 1
                        continue
                    best_time = datetime.datetime.strptime(row[4], "%M:%S.%f")
                    s1 = datetime.datetime.strptime(row[5], "%M:%S.%f")
                    s2 = datetime.datetime.strptime(row[6], "%M:%S.%f")
                    s3 = datetime.datetime.strptime(row[7], "%M:%S.%f")
                    
                    entry = Entry(
                        name=row[1],\
                        id=row[2],\
                        car=row[3],\
                        best_time=datetime.timedelta(minutes=best_time.minute, seconds=best_time.second, microseconds=best_time.microsecond),\
                        s1=datetime.timedelta(minutes=s1.minute, seconds=s1.second, microseconds=s1.microsecond),\
                        s2=datetime.timedelta(minutes=s2.minute, seconds=s2.second, microseconds=s2.microsecond),\
                        s3=datetime.timedelta(minutes=s3.minute, seconds=s3.second, microseconds=s3.microsecond)\
                    )
                    #print(entry)
                    entry_list.append(entry)
                line_count += 1
        #last_updated = datetime.datetime.strptime(last_updated_str, "%Y-%m-%dT%H:%M:%S%z")
        last_updated = parser.parse(last_updated_str)
        return cls(file_path=file_path, entry_list=entry_list, last_updated=last_updated)

    def generate_embed_compatible(self):
        Embed = namedtuple("Embed", "driver car time")
        driver_str = f""
        car_str = f""
        time_str = f""
        for entry in self.entry_list:
            driver_str += f"{entry.name}\n"
            car_str += f"{entry.car}\n"
            time_str += f"{laptimetostring(entry.best_time)}\n"
        Embed.driver = driver_str
        Embed.car = car_str
        Embed.time = time_str
        return Embed

    def write_leaderboard(self, file_path: None, suppress_id = False, space_delim = False, include_timestamp = True, trail_trim = False):
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
        with open(file_path, "w") as file:
            file.write(self.__str__(suppress_id=suppress_id, space_delim=space_delim, include_timestamp=include_timestamp, trail_trim=trail_trim))

    def __str__(self, suppress_id = False, space_delim = False, short = False, include_timestamp = True, trail_trim = False) -> str:
        """
        Convert the leaderboard to a csv string

        Args:
            suppress_id: Suppress driver ID flag
            space_delim: Space delimited mode
            include_timestamp: Include last updated timestamp line flag
            trail_trim: Trim trailing zeroes flag
        Return:
            CSV string
        """
        us_div = 1
        #Justification modifier
        just_mod = 0
        if trail_trim:
            us_div = 1000
            just_mod = 3
        if space_delim:
            name_max_width = 0
            car_max_width = 0
            for entry in self.entry_list:
                name = entry.name
                car = entry.car
                if len(name) > name_max_width:
                    name_max_width = len(name)
                if len(car) > car_max_width:
                    car_max_width = len(car)
            if suppress_id:
                csv_header = constants.csv_header_no_id
                columns = csv_header.split(',')
                # 18 is the max width of time in MM:ss.SSSSSS format
                # Justification stuff
                leaderboard_str = (
                    f"{str(columns[0]).center(6,' ')}"
                    f"{str(columns[1]).center(name_max_width+4,' ')}"
                    f"{str(columns[2]).center(car_max_width+4,' ')}"
                    f"{str(columns[3]).center(18-just_mod,' ')}"
                    f"{str(columns[4]).center(18-just_mod,' ')}"
                    f"{str(columns[5]).center(18-just_mod,' ')}"
                    f"{str(columns[6]).center(18-just_mod,' ')}"
                    f"\n"
                )
            else:
                #Not supported cuz who tf would want that
                return "BITCH WHAT THE FUCK"
            last_updated_str = datetime.datetime.strftime(self.last_updated, "%Y-%m-%dT%H:%M:%S%z")
            rank = 1
            for entry in self.entry_list:
                #leaderboard_str += f"{rank},{entry.__str__(suppress_id=suppress_id)}\n"
                leaderboard_str += (
                    f"{str(rank).center(6, ' ')}"
                    f"{str(entry.name).ljust(name_max_width+4, ' ')}"
                    f"{str(entry.car).ljust(car_max_width+4, ' ')}"
                    f"{laptimetostring(entry.best_time, trail_trim).center(18-just_mod, ' ')}"
                    f"{laptimetostring(entry.s1, trail_trim).center(18-just_mod, ' ')}"
                    f"{laptimetostring(entry.s2, trail_trim).center(18-just_mod, ' ')}"
                    f"{laptimetostring(entry.s3, trail_trim).center(18-just_mod, ' ')}"
                    f"\n"
                )
                rank += 1
            if include_timestamp:
                leaderboard_str += f"Last updated?{last_updated_str}\n"
            return leaderboard_str
        else:
            if not suppress_id:
                leaderboard_str = constants.csv_header + "\n"
            else:
                leaderboard_str = constants.csv_header_no_id + "\n"
            last_updated_str = datetime.datetime.strftime(self.last_updated, "%Y-%m-%dT%H:%M:%S%z")
            rank = 1
            for entry in self.entry_list:
                leaderboard_str += f"{rank},{entry.__str__(suppress_id=suppress_id, trail_trim=trail_trim)}\n"
                rank += 1
            if include_timestamp:
                leaderboard_str += f"Last updated?{last_updated_str}\n"
            return leaderboard_str

    def update(self, pages = 3, pw = True):
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
        for page in range(0, pages):
            print(f"=====Processing page{page+1}=====")
            dash_html = requests.get(f"{Session.dash_url}?page={page}", allow_redirects=True).content.decode("utf-8")
            soup = bs4.BeautifulSoup(dash_html, "html.parser")
            rows = soup.select(".row-link")
            for row in rows:
                filename = row['data-href'].split('/')[2]
                #track_excludes = constants.session_exclude[self.track]
                if (filename in constants.session_exclude[self.track]):
                    print(f"DB: Excluded session || {Session.session_res_prefix}{filename}")
                    continue
                session_res_url = f"{Session.session_res_prefix}{filename}"
                session_res_html = requests.get(session_res_url, allow_redirects=True).content.decode("utf-8")
                if (
                    pw and
                    ("Password: sra" not in session_res_html) and 
                    ("SRA League Race" not in session_res_html)
                ):
                    print(f"DB: No password || {Session.session_res_prefix}{filename}")
                    continue
                print(f"Processing: {Session.session_res_prefix}{filename}")
                children = row.contents
                timestamp_str = children[1].contents[0].strip()
                session_type = children[3]
                track = children[5].contents[0].strip()
                #timestamp = datetime.datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S %Z")
                timestamp = parser.parse(timestamp_str)

                if ( (track == self.track) and (timestamp > self.last_updated) ):   #If track matches and new
                    session = Session(filename)
                    session.get_session_results()
                    if not session.results:
                        continue
                    if not self.entry_list:
                        self.entry_list = session.results
                        continue
                    for session_entry in session.results:
                        found_flag = False
                        for leaderboard_entry in self.entry_list:
                            # If car and ID match
                            if ( (leaderboard_entry.id == session_entry.id) and (leaderboard_entry.car == session_entry.car) ):
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
                    print(f"DB: Track doesn't match || {Session.session_res_prefix}{filename}")
            print(f"=====Finished page{page+1}=====")
        self.entry_list.sort(key=lambda x: x.best_time.total_seconds())
        self.last_updated = datetime.datetime.now(datetime.timezone.utc)
        return

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
        pandas_csv = pandas.read_csv(html_csv_path, encoding='latin1')
        pandas_html = pandas_csv.to_html(None, index=False, justify='center', classes="ldb-table")
        with open(html_path, "w", encoding="utf-8") as html_file:
            html_file.write(constants.html_string.format(ldb_html=pandas_html))
        return

                

def main():

    leaderboard = Leaderboard.read_leaderboard(path.join("csvs", "Brands Hatch.csv"))
    leaderboard.track = "Silverstone"
    leaderboard.update(pages=1)
    #leaderboard.update()
    #leaderboard.write_leaderboard(file_path=path.join("ready", f"{leaderboard.track}.txt"), suppress_id=True, space_delim=True, trail_trim=True)
    #embed = leaderboard.generate_embed_compatible()
    #print(embed.driver)
    #print(embed.car)
    #print(embed.time)

if __name__ == "__main__":
    main()