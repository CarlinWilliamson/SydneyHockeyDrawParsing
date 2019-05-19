from ics import Calendar, Event
import re
import PyPDF2
import pytz
import datetime

GROUNDS = ["Pennant Hills 1", "Pennant Hills 2", "Sutherland", "Ryde", "Cintra Park", "Lidcombe", "Bankstown", "Olympic 1", "Olympic 2", "Daceyville"]

TEAM_REPLACEMENTS = {"UNSW":"Unsw", "UTS":"Uts", "Northern Districts":"Northerndistricts", "NWS/Baulkham Hills":"NWSBaulkhamhills", "Ryde HH":"Ryde"}

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
		self.time = time
		self.home = home
		self.away = away
	
	def __str__(self):
		return "{} {} {}\n{} vs {}".format(self.time, self.date, self.ground, self.home, self.away)

pdf = ""

with open("doc.pdf", 'rb') as f:
	reader = PyPDF2.PdfFileReader(f)
	for page in reader.pages:
		pdf += page.extractText()

pdf = re.sub(r'Accessed.*?of \d\d', r'', pdf)
pdf = re.sub(r'Round.*?\d\d\d\d', r'', pdf)
pdf = re.sub(r'Pitch ', r'', pdf)

for key, value in TEAM_REPLACEMENTS.items():
        pdf = pdf.replace(key, value)

ground_indexes = []
for ground in GROUNDS:
	ground = ground + "D" # avoid teams that have the same name as a ground
	for match in re.finditer(ground, pdf):
		ground_indexes.append(match.start())

matches = []
ground_indexes.sort()

for i, index in enumerate(ground_indexes):
	g = ""
	if (i == len(ground_indexes)-1):
		g = pdf[index:]
	else:
		g = pdf[index:ground_indexes[i+1]]

	for (ground, date, time, home, away, other) in re.findall(r'(.*?)DayTimeHomeAway(.*?)(\d\d:\d\d)([A-Z\/]+[a-z_]*)([A-Z\/]+[a-z_]*)(.*)', g):
		matches.append(Game(ground, date, time, home, away))
		while (len(other) > 5):
			reg = re.search(r'(.*?)(\d\d:\d\d)([A-Z\/]+[a-z_]*)([A-Z\/]+[a-z_]*)(.*)', other)
			matches.append(Game(ground, reg.group(1), reg.group(2), reg.group(3), reg.group(4)))
			other = reg.group(5)

c = Calendar()
print(len(matches))
for match in matches:
	e = Event(name="{} vs {}".format(match.home, match.away), begin=match.date, location=match.ground)
	c.events.add(e)


with open('matches.ics', 'w') as my_file:
	my_file.writelines(c)
