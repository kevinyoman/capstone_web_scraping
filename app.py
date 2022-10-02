from flask import Flask, render_template
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64
from bs4 import BeautifulSoup 
import requests
import datetime

#don't change this
matplotlib.use('Agg')
app = Flask(__name__) #do not change this

#insert the scrapping here
url_get = requests.get('https://www.imdb.com/search/title/?release_date=2021-01-01,2021-12-31&count=250')
soup = BeautifulSoup(url_get.content,"html.parser")

#find your right key here
table = soup.find('div', attrs={'class':'lister-list'})
judul_all = table.find_all('h3', attrs={'class':'lister-item-header'})
metascore_bar = table.find_all('div', attrs={'class':'ratings-bar'})
row_length = len(judul_all)

# function to call page that has information about release date
def get_releasedate(title_rellink):
    url_rd = f'''https://www.imdb.com/title/{title_rellink}/releaseinfo?ref_=tt_dt_rdat'''
    release_get = requests.get(url_rd)
    soup_rd = BeautifulSoup(release_get.content,"html.parser")
    table_rd = soup_rd.find_all('tr', attrs={'class':'ipl-zebra-list__item release-date-item'})
    rd_length=len(table_rd)
    
    release_date = ''
    for i in range(0,rd_length):
        # only date from region USA
        get_region = table_rd[i].find_all('td')[0].find('a')['href'].split('region=')[1]
        if get_region == 'us':
            rd = table_rd[i].find_all('td')[1].text.split(' ')
            release_date = f'''{rd[0]}-{rd[1]}'''
    return release_date

temp = [] #initiating a list 

for i in range(0, row_length):
	# rank by popularity in imdb website
    rank = i + 1; 
    
    # get title
    judul = judul_all[i].text.strip().split('\n')[1]
    
    # get relation link of title      
    judul_link = judul_all[i].find('a')['href'].split('/')[2]
    release_date = get_releasedate(judul_link)

    imdb_rating = metascore_bar[i].find('meta', attrs={'itemprop':'ratingValue'})['content']
    votes = metascore_bar[i].find('meta', attrs={'itemprop':'ratingCount'})['content']

    find_metascore = metascore_bar[i].find_all('span', attrs={'class':'metascore favorable'})
    metascore = find_metascore[0].text.strip() if (find_metascore) else 0
    
    temp.append((rank,judul,imdb_rating,metascore,votes,release_date))

#change into dataframe
col_movie = ['rank','title','imdb','metascore','votes','release_date']
df = pd.DataFrame(temp,columns=col_movie)

#insert data wrangling here
missing_date = df[df['release_date'] == '']
df.drop(missing_date.index,axis=0, inplace=True)

check_itf = df['release_date'].apply(lambda x: x.split('-')[1])
index_itf = check_itf[check_itf == '2022'].index
release_itf = df.loc[index_itf]
df.drop(release_itf.index,axis=0, inplace=True)

get_day = df['release_date'].apply(lambda x : str(x.split('-')[0]).zfill(2))
get_month = df['release_date'].apply(lambda x : x.split('-')[1])
get_month = get_month.apply(lambda x : str(datetime.datetime.strptime(x, '%B').month).zfill(2))
df['release_date'] = '2021-'+get_month+'-'+get_day
df['release_date'] = df['release_date'].astype('datetime64')

remove_series = df[df['metascore'] != 0]
remove_series = remove_series.reset_index()
remove_series['rank'] = remove_series.index+1
movie = pd.DataFrame(remove_series,columns=col_movie)

movie[['imdb','metascore']] = movie[['imdb','metascore']].astype('float64')
movie[['votes']] = movie[['votes']].astype('int64')
movie['metascore'] = movie['metascore'] / 10
movie['metascore'] = movie['metascore'].round(1)
#end of data wranggling 

movie['rank_title'] = movie[['title','rank']].apply(lambda x : ' (rank '.join(x.astype('str').values),axis=1) + ')'
topby_rank = movie.head(7)
top_imbdb = movie.sort_values('imdb',ascending=False).head(7)
top_ms = movie.sort_values('metascore',ascending=False).head(7)
x_topimdb = top_imbdb['rank_title']
y_topimdb = top_imbdb['imdb']
x_topms = top_ms['rank_title']
y_topms = top_ms['metascore']
hist_imdb = movie['imdb']
hist_ms = movie['metascore']

@app.route("/")
def index(): 
	# card_data = f'{df_clean["imdb"].mean().round(2)}' #be careful with the " and ' 
	card_data = 'Popular Movie'

	# generate plot barh rank
	plt.clf()
	fig, ax = plt.subplots()
	width = 0.2 
	x = np.arange(topby_rank['title'].size)

	ax.barh(x, topby_rank['imdb'], width, color='#000080', label='imdb')
	ax.barh(x + width, topby_rank['metascore'], width, color='#0F52BA', label='metascore')
	ax.set_yticks(x + width - (width/2))
	ax.set_yticklabels(topby_rank['rank_title'])
	ax.set_xlabel('ratings')
	ax.legend()
	# Rendering plot
	# Do not change this
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_rank = str(figdata_png)[2:-1]

	# generate plot barh imdb
	plt.clf()
	plt.barh(x_topimdb,y_topimdb)
	plt.xlabel('ratings')
	# Rendering plot
	# Do not change this
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_imdb = str(figdata_png)[2:-1]
    
	# generate plot barh metascore
	plt.clf()
	plt.barh(x_topms,y_topms) 
	plt.xlabel('ratings')
	# Rendering plot
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_ms = str(figdata_png)[2:-1]

	# generate plot scatter rank vs imdb
	plt.clf()
	plt.scatter(movie['imdb'],movie['rank'])
	plt.ylabel('ranks')
	plt.xlabel('imdb ratings')
	# Rendering plot
	# Do not change this
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_scimdb = str(figdata_png)[2:-1]
    
	# generate plot scatter rank vs metascore
	plt.clf()
	plt.scatter(movie['metascore'],movie['rank'])
	plt.ylabel('ranks')
	plt.xlabel('metascore ratings')
	# Rendering plot
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_scms = str(figdata_png)[2:-1]

	# generate plot scatter rank vs release_date
	plt.clf()
	fig, ax = plt.subplots()
	ax.scatter(movie['release_date'],movie['rank'])
	ax.set_xticklabels(['2021-01','2021-03','2021-05','2021-07','2021-09','2021-11','2021-12'])
	ax.set_xlabel('release date')
	ax.set_ylabel('ranks')
	# Rendering plot
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_scdate = str(figdata_png)[2:-1]

	# generate plot histogram
	plt.clf()
	plt.hist(hist_imdb) 
	plt.title("imdb")
	# Rendering plot
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_hist_imdb = str(figdata_png)[2:-1]

	plt.clf()
	plt.hist(hist_ms) 
	plt.title('metascore')
	# Rendering plot
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_hist_ms = str(figdata_png)[2:-1]

	# render to html
	return render_template('index.html',
		card_data = card_data, 
		plot_rank = plot_rank,
		plot_imdb = plot_imdb, 
        plot_ms = plot_ms,  
		plot_scimdb = plot_scimdb,
		plot_scms = plot_scms,
		plot_scdate = plot_scdate, 
		plot_hist_imdb = plot_hist_imdb, 
        plot_hist_ms = plot_hist_ms                 
		)


if __name__ == "__main__": 
    app.run(debug=True)