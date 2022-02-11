## Structure

### Entry object
- Name
- ID
- Car
- Best time

### Session object
- List of Entries

### Leaderboard object
- Track
- Last updated time
- List of entries
- File path

### read_leaderboard(file)
- Parse leaderboard csv file into leaderboard object

### update_leaderboard()
- Get dash html code
- Get table rows from html code
  - Table row
    - Date
    - Type
    - Result page link
  - If (date > leaderboard.date) && (track == leaderboard.track)
    - Go to result page
    - Get session result html
    - If contain password
      - Fetch results/download/json
      - Parse "leaderboardLines
        - Name - playerID - Car -> List of entry objects
      - Loop through laps to find best lap for each driver
      - Compare CSV entries with json entries
        - If name and car matches -> Update json object with best time
  - Sort objects by best time

### write_leaderboard(leaderboard)
- Write leaderboard object to CSV file

### @bot.command print_leaderboard(track)
- Read track name
- Construct file name from track name
- Call read_leaderboard(file)
- Convert object to csv text
- Print text

### @bot.command update_leaderboard(track)
- Read track name
- Construct filename from track name
- Call read_leaderboard(file)
- Update leaderboard
- Write new leaderboard

### @bot.command genscr(track)
- Read track name
- Read leaderboard
- Convert leaderboard to html with only essential columns
- Use headless browser to render html and take a screenshot
- Send screenshot

## TODO:
- Have a list of all registered drivers steamID to filter randoms from open lobbies
- ~~Experiment with headless browsers~~
- Faster search and match (binary search?)
- Rolling backups with timestamps
- Error messages for non-ideal users

## Reference:
- Server results dashboard url: https://simracingalliance.emperorservers.com/results
- Session results url: https://simracingalliance.emperorservers.com/results/220119_025358_Q
- Session results json url: https://simracingalliance.emperorservers.com/results/download/220119_025358_Q.json