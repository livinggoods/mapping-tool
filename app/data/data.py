import csv, os

def get_locations():
  with open(os.path.abspath(os.path.dirname(__file__))+'/data.csv', 'r') as f:
    data_numbers = {}
    districts = {}
    counties = {}
    sub_counties = {}
    for row in csv.reader(f.read().splitlines()):
      data_numbers[row[3]]= {'county':row[2], 'district':row[1], 'number':row[0]}
      if row[1] in districts:
        if row[2] in districts.get(row[1]):
          districts[row[1]][row[2]].append({'name':row[3], 'number':row[0]})
        else:
          districts[row[1]][row[2]] = []
          districts[row[1]][row[2]].append({'name':row[3], 'number':row[0]})
      else:
        districts[row[1]] = {}
        districts[row[1]][row[2]] = []
        districts[row[1]][row[2]].append({'name':row[3], 'number':row[0]})
  return districts

def get_ke_counties():
  counties = []
  with open(os.path.abspath(os.path.dirname(__file__))+'/kenya_county.csv', 'r') as f:
    for row in csv.reader(f.read().splitlines()):
      # county = {}
      counties.append({'name': row[1], 'code': row[0]})
  return counties
