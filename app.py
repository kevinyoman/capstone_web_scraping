from flask import Flask, render_template
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from bs4 import BeautifulSoup 
import requests

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

temp = [] #initiating a list 

for i in range(1, row_length):
#insert the scrapping process here
    judul = judul_all[i].text.strip().split('\n')[1]

    imdb_rating = metascore_bar[i].find('meta', attrs={'itemprop':'ratingValue'})['content']
    votes = metascore_bar[i].find('meta', attrs={'itemprop':'ratingCount'})['content']

    find_metascore = metascore_bar[i].find_all('span', attrs={'class':'metascore favorable'})
    metascore = find_metascore[0].text.strip() if (find_metascore) else 'missing' 
    
    temp.append((judul,imdb_rating,metascore,votes))

temp = temp[::-1]

#change into dataframe
col_movie = ['title','imdb','metascore','votes']
df = pd.DataFrame(temp, columns = col_movie)

#insert data wrangling here
df_clean = df[df['metascore'] != 'missing']

df_clean[['imdb','metascore']] = df_clean[['imdb','metascore']].astype('float64')

df_clean['metascore'] = df_clean['metascore'] / 10
df_clean['metascore'] = df_clean['metascore'].round(1)

df_novotes = df_clean.drop('votes',axis=1)
#end of data wranggling 

top_imbdb = df_novotes.sort_values('imdb',ascending=False).head(7)
top_ms = df_novotes.sort_values('metascore',ascending=False).head(7)
x_topimdb = top_imbdb['title']
y_topimdb = top_imbdb['imdb']
x_topms = top_ms['title']
y_topms = top_ms['metascore']
hist_imdb = df_novotes['imdb']
hist_ms = df_novotes['metascore']

@app.route("/")
def index(): 
	
	# card_data = f'{df_clean["imdb"].mean().round(2)}' #be careful with the " and ' 
	card_data = 'imdb vs metascore'

	# generate plot imdb
	plt.clf()
	plt.barh(x_topimdb,y_topimdb)
	# Rendering plot
	# Do not change this
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_imdb = str(figdata_png)[2:-1]
    
	# generate plot metascore
	plt.clf()
	plt.barh(x_topms,y_topms) 
	# Rendering plot
	figfile = BytesIO()
	plt.savefig(figfile, format='png', transparent=True, bbox_inches='tight')
	figfile.seek(0)
	figdata_png = base64.b64encode(figfile.getvalue())
	plot_ms = str(figdata_png)[2:-1]

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
		plot_imdb = plot_imdb, 
        plot_ms = plot_ms,  
		plot_hist_imdb = plot_hist_imdb, 
        plot_hist_ms = plot_hist_ms                 
		)


if __name__ == "__main__": 
    app.run(debug=True)