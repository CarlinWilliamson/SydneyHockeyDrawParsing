from ics import Calendar, Event
import re
import PyPDF2
import pytz
import datetime
import argparse

GROUNDS = ["Pennant Hills 1", "Pennant Hills 2", "Sutherland", "Ryde", "Cintra Park", "Lidcombe", "Bankstown", "Olympic 1", "Olympic 2", "Daceyville", "Kyeemagh", "Greenhills \(Marang Parkland\)"]

# To make the regex easier we convert team names to a Capital letter followed by lower case letters with no spaces
TEAM_REPLACEMENTS = {"UNSW":"Unsw", "UTS":"Uts", "Northern Districts":"Northerndistricts", "NWS/Baulkham Hills":"NWSBaulkhamhills", "Ryde HH":"Ryde", "St George/Rand":"Stgeorgerand", "Macquarie Uni":"Macquarieuni", "Ryde White":"Rydewhite", "Ryde Black":"Rydeblack", "Sydney Uni":"Sydneyuni", "GNS":"Gns", "Moorebank Liverpool":"Moorebankliverpool", "NWS/BH":"Nwsbh"}
INV_TEAM_REPLACEMENTS = {j: k for k,j in TEAM_REPLACEMENTS.items()}

MONTH_TO_NUMBER = {"Jan":1, "Feb":2, "Mar":3, "Apr":4, "May":5, "Jun":6, "Jul":7, "Aug":8, "Sep":9, "Oct":10, "Nov":11, "Dec":12}

class Game:
	date = None
	time = None
	ground = None
	home = None
	away = None
	def __init__(self, ground, date, time, home, away):

		reg = re.search(r'(\d\d) (\w\w\w)(\d\d\d\d)', date)
		year = int(reg.group(3))
		month = MONTH_TO_NUMBER.get(reg.group(2))
		day = int(reg.group(1))
		hours = int(time.split(":")[0])
		minutes = int(time.split(":")[1])
		d = datetime.datetime(year, month, day, hours, minutes)
		timezone = pytz.timezone("Australia/Sydney")

		self.date = timezone.localize(d)
		self.ground = ground

		# change the team names back
		self.home = INV_TEAM_REPLACEMENTS.get(home, home)
		self.away = INV_TEAM_REPLACEMENTS.get(away, away)
	
	def __str__(self):
		return "{} {}\n{} vs {}\n".format(self.date, self.ground, self.home, self.away)

parser = argparse.ArgumentParser(description='Convert a pdf of a Sydney Hockey draw into an ical')
parser.add_argument("filename", help='the file from which the ical should be created')
parser.add_argument('--team', dest='team', help='specify a team for which the events are parse')
args = parser.parse_args()


# read the pdf and create one long string
pdf = ""
with open(args.filename, 'rb') as f:
	reader = PyPDF2.PdfFileReader(f)
	for page in reader.pages:
		pdf += page.extractText()

# remove the junk that is at the start/end of each page
pdf = re.sub(r'Accessed.*?of \d\d', r'', pdf)
pdf = re.sub(r'Round.*?\d\d\d\d', r'', pdf)

# The fields at olympic park appear as "Olympic 1" and "Olympic Pitch 2"
# changing them to be the same 
pdf = re.sub(r'Pitch ', r'', pdf)

# Apply the dictionary to the whole string
for key, value in TEAM_REPLACEMENTS.items():
        pdf = pdf.replace(key, value)

ground_indexes = []
for ground in GROUNDS:
	ground = ground + "D" # avoid teams that have the same name as a ground
	for match in re.finditer(ground, pdf):
		ground_indexes.append(match.start())


# between each of the indexes in ground_indexes is information about all the games at that ground in that grade
matches = []
ground_indexes.sort()
for i, index in enumerate(ground_indexes):
	
	# create a string from the start of one ground to the next
	g = ""
	if (i == len(ground_indexes)-1):
		g = pdf[index:] # avoid index out of bound error
	else:
		g = pdf[index:ground_indexes[i+1]]

	for (ground, date, time, home, away, other_games) in re.findall(r'(.*?)DayTimeHomeAway(.*?)(\d\d:\d\d)([A-Z\/]+[a-z_]*)([A-Z\/]+[a-z_]*)(.*)', g):
		matches.append(Game(ground, date, time, home, away))

		# There can be more than one game at a specific ground in that round
		# keep parsing those games until we run out of them
		while len(other_games) > 5:
			reg = re.search(r'(.*?)(\d\d:\d\d)([A-Z\/]+[a-z_]*)([A-Z\/]+[a-z_]*)(.*)', other_games)
			matches.append(Game(ground, reg.group(1), reg.group(2), reg.group(3), reg.group(4)))
			other_games = reg.group(5)

# convert our list of matches into a iCalendar
c = Calendar()
for match in matches:
	name = ""
	if not args.team:
		name = "{} vs {}".format(match.home, match.away)
	elif args.team in match.home:
		name = "{} vs {}".format(args.team, match.away)
	elif args.team in match.away:
		name = "{} vs {}".format(args.team, match.home)
	else:
		continue

	e = Event(name=name, begin=match.date, location=match.ground)
	c.events.add(e)

with open(args.filename.split(".")[0] + ".ics", "w") as my_file:
	my_file.writelines(c)
