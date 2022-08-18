from flask import Flask, render_template, request, url_for, redirect
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import joblib
from datetime import date
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bandung12'




    



@app.route("/", methods=["GET","POST"])
def home():
    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']
        province = request.form['province']
        city = request.form['city']
        produk = request.form['produk']
        qty = request.form['qty']
        message = request.form['message']

        produk = produk.split(', ')

        # request data
        df_orders = pd.read_csv('datasets/orders.csv')

        # data cleaning
        df_orders = df_orders.loc[:, ["province", "city", "status", "courier","order_via","shipping_cost",'weight','quantity','name']]

        df_orders['shipping_cost'].fillna(df_orders['shipping_cost'].median(), inplace=True)
        df_orders["status"] = df_orders["status"].apply(lambda x: "Return" if x == "retur_verify" else "Success")
        df_orders["status"].value_counts()
        df_orders["city"] = df_orders["city"].apply(lambda x: x.replace("Kab.","Kabupaten") if "Kab." in x else x)


        # Shuffle the Dataset.
        shuffled_df = df_orders.sample(frac=1,random_state=4)

        # Put all the fraud class in a separate dataset.
        jne_df = shuffled_df.loc[shuffled_df['courier'] == "jne"]

        #Randomly select 492 observations from the non-fraud (majority class)
        jnt_df = shuffled_df.loc[shuffled_df['courier'] == "J&T"].sample(n=27588,random_state=42)

        # Concatenate both dataframes again
        df_orders = pd.concat([jne_df, jnt_df])
    


        # return rate
        df_orders = df_orders.join((df_orders.loc[(df_orders["status"] == "Return") & (df_orders["courier"] == "jne") , "province"].value_counts() / df_orders.loc[df_orders["courier"] == "jne", "province"].value_counts())
                    .rename("jne_retur_rate").to_frame(), on="province").join((df_orders.loc[(df_orders["status"] == "Return") & (df_orders["courier"] == "J&T") , "province"].value_counts() / df_orders.loc[df_orders["courier"] == "J&T", "province"].value_counts())
                    .rename("jnt_retur_rate").to_frame(), on="province")
        df_orders = df_orders.fillna(0)
        df_orders['jne_retur_rate'] = df_orders['jne_retur_rate'].fillna(0)
        df_orders.loc[df_orders['province'] == "Nusa Tenggara Barat (NTB)", ['jne_retur_rate']] = 0.05125
        df_orders.loc[df_orders['province'] == "Bangka Belitung", ['jne_retur_rate']] = 0.018471
        df_orders.loc[df_orders['province'] == "Jawa Timur", ['jnt_retur_rate']] = 0.079232
        df_orders.loc[df_orders['province'] == "Lampung", ['jnt_retur_rate']] = 0.092386
        df_orders.loc[df_orders['province'] == "Jambi", ['jne_retur_rate']] = 0.03954

        inputs = df_orders.drop(["status","courier",'weight','quantity','name'], axis="columns")

        # Encoding data
        le_province = LabelEncoder()
        le_cities = LabelEncoder()

        # creates new columns for encoding data
        inputs['province_n'] = le_province.fit_transform(inputs['province'])
        inputs['cities_n'] = le_cities.fit_transform(inputs['city'])

        


        # load the model from disk
        filename = 'finalized_model.sav'
        loaded_model = joblib.load(filename)
        print(province)
        print(city)

        try:
            row_jne = inputs.loc[(inputs["province"] == province.strip()) & (inputs['city'] == city.strip()), :]["jne_retur_rate"].min().astype(float)
            row_jnt = inputs.loc[(inputs["province"] == province.strip()) & (inputs['city'] == city.strip()), :]["jnt_retur_rate"].min().astype(float)

            class_names={0:"J&T", 1:"jne"}
            if (row_jne > row_jnt):
                result = 0
            else:
                result = 1
            
            shipping_cost = int(df_orders.loc[(df_orders['courier'] == class_names[result]) & (inputs["province"] == province.strip()) & (inputs['city'] == city.strip()), ['city','shipping_cost']].drop_duplicates()[~(df_orders['shipping_cost']==0)]['shipping_cost'].min()) * int(qty)

            return redirect(url_for('invoice', data=json.dumps({"name": first_name + " "+last_name,"email":email,"phone":phone,"province":province,"city":city,"produk":produk[0],"price":produk[1], "courier":class_names[result], "shipping_cost":shipping_cost, "qty":int(qty),"message":message})))

    

        except:
            return render_template("error.html")
       

        

       
    return render_template("input_order.html")

@app.route("/invoice", methods=["GET"])
def invoice():
    data = request.args.get('data')
    print(data)
    data = json.loads(data)
    subtotal = int(data['price']) * int(data['qty'])
    return render_template('invoice.html', data=data, subtotal=subtotal, total= subtotal + int(data['shipping_cost']), date=date.today())

@app.route("/locations", methods=["GET"])
def locations():
    return  {'Bali': ['Kota Denpasar', ' Kabupaten Karangasem', ' Kabupaten Jembrana', ' Kabupaten Badung', ' Kabupaten Gianyar', ' Kabupaten Tabanan', ' Kabupaten Buleleng', ' Kabupaten Bangli', ' Kabupaten Klungkung'], 'Bangka Belitung': ['Kota Pangkal Pinang', ' Kabupaten Bangka', ' Kabupaten Belitung', ' Kabupaten Bangka Selatan', ' Kabupaten Bangka Barat', ' Kabupaten Bangka Tengah', ' Kabupaten Belitung Timur'], 'Banten': ['Kabupaten Tangerang', ' Kabupaten Pandeglang', ' Kota Tangerang', ' Kabupaten Serang', ' Kota Tangerang Selatan', ' Kabupaten Lebak', ' Kota Serang', ' Kota Cilegon'], 'Bengkulu': ['Kota Bengkulu', ' Kabupaten Bengkulu Utara', ' Kabupaten Kepahiang', ' Kabupaten Seluma', ' Kabupaten Muko Muko', ' Kabupaten Bengkulu Selatan', ' Kabupaten Rejang Lebong', ' Kabupaten Kaur', ' Kabupaten Lebong', ' Kabupaten Bengkulu Tengah'], 'DI Yogyakarta': ['Kabupaten Sleman', ' Kabupaten Kulon Progo', ' Kota Yogyakarta', ' Kabupaten Bantul', ' Kabupaten Gunung Kidul'], 'DKI Jakarta': ['Kota Jakarta Utara', ' Kota Jakarta Timur', ' Kota Jakarta Selatan', ' Kota Jakarta Barat', ' Kota Jakarta Pusat', ' Kabupaten Kepulauan Seribu'], 'Gorontalo': ['Kabupaten Gorontalo Utara', ' Kota Gorontalo', ' Kabupaten Pohuwato', ' Kabupaten Gorontalo', ' Kabupaten Bone Bolango', ' Kabupaten Boalemo'], 'Jambi': ['Kota Jambi', ' Kabupaten Sarolangun', ' Kabupaten Bungo', ' Kabupaten Muaro Jambi', ' Kabupaten Tanjung Jabung Timur', ' Kabupaten Batang Hari', ' Kabupaten Tanjung Jabung Barat', ' Kabupaten Tebo', ' Kabupaten Kerinci', ' Kabupaten Merangin', ' Kota Sungaipenuh'], 'Jawa Barat': ['Kabupaten Bekasi', ' Kabupaten Subang', ' Kabupaten Cirebon', ' Kota Bekasi', ' Kota Cirebon', ' Kota Bogor', ' Kabupaten Bandung', ' Kabupaten Bogor', ' Kota Tasikmalaya', ' Kabupaten Indramayu', ' Kota Cimahi', ' Kabupaten Sukabumi', ' Kabupaten Karawang', ' Kota Depok', ' Kabupaten Sumedang', ' Kabupaten Majalengka', ' Kabupaten Garut', ' Kabupaten Tasikmalaya', ' Kabupaten Ciamis', ' Kota Bandung', ' Kabupaten Bandung Barat', ' Kabupaten Cianjur', ' Kabupaten Purwakarta', ' Kabupaten Kuningan', ' Kabupaten Pangandaran', ' Kota Banjar', ' Kota Sukabumi'], 'Jawa Tengah': ['Kabupaten Batang', ' Kabupaten Kudus', ' Kota Pekalongan', ' Kabupaten Blora', ' Kota Semarang', ' Kabupaten Semarang', ' Kabupaten Rembang', ' Kabupaten Banyumas', ' Kabupaten Cilacap', ' Kabupaten Wonosobo', ' Kabupaten Pekalongan', ' Kabupaten Grobogan', ' Kabupaten Sukoharjo', ' Kabupaten Brebes', ' Kabupaten Tegal', ' Kota Tegal', ' Kabupaten Magelang', ' Kota Surakarta (Solo)', ' Kabupaten Pati', ' Kabupaten Banjarnegara', ' Kabupaten Demak', ' Kota Salatiga', ' Kabupaten Kebumen', ' Kabupaten Klaten', ' Kabupaten Sragen', ' Kabupaten Karanganyar', ' Kabupaten Wonogiri', ' Kabupaten Purbalingga', ' Kabupaten Pemalang', ' Kabupaten Kendal', ' Kabupaten Temanggung', ' Kota Magelang', ' Kabupaten Boyolali', ' Kabupaten Purworejo', ' Kabupaten Jepara'], 'Jawa Timur': ['Kota Surabaya', ' Kabupaten Pamekasan', ' Kabupaten Ngawi', ' Kabupaten Malang', ' Kota Blitar', ' Kabupaten Banyuwangi', ' Kabupaten Bangkalan', ' Kabupaten Sumenep', ' Kabupaten Gresik', ' Kota Malang', ' Kabupaten Probolinggo', ' Kabupaten Lumajang', ' Kabupaten Jombang', ' Kabupaten Sidoarjo', ' Kabupaten Ponorogo', ' Kabupaten Mojokerto', ' Kabupaten Jember', ' Kabupaten Tulungagung', ' Kabupaten Blitar', ' Kabupaten Kediri', ' Kabupaten Tuban', ' Kabupaten Situbondo', ' Kabupaten Bojonegoro', ' Kabupaten Bondowoso', ' Kota Batu', ' Kabupaten Pasuruan', ' Kabupaten Pacitan', ' Kabupaten Nganjuk', ' Kabupaten Trenggalek', ' Kabupaten Lamongan', ' Kabupaten Sampang', ' Kota Probolinggo', ' Kota Pasuruan', ' Kota Kediri', ' Kabupaten Madiun', ' Kota Madiun', ' Kabupaten Magetan', ' Kota Mojokerto'], 'Kalimantan Barat': ['Kabupaten Sintang', ' Kabupaten Sambas', ' Kabupaten Ketapang', ' Kabupaten Sanggau', ' Kota Singkawang', ' Kabupaten Sekadau', ' Kabupaten Kapuas Hulu', ' Kabupaten Bengkayang', ' Kota Pontianak', ' Kabupaten Landak', ' Kabupaten Kayong Utara', ' Kabupaten Pontianak', ' Kabupaten Kubu Raya', ' Kabupaten Melawi'], 'Kalimantan Selatan': ['Kabupaten Banjar', ' Kota Banjarbaru', ' Kabupaten Tanah Laut', ' Kabupaten Tapin', ' Kota Banjarmasin', ' Kabupaten Tanah Bumbu', ' Kabupaten Tabalong', ' Kabupaten Hulu Sungai Selatan', ' Kabupaten Kotabaru', ' Kabupaten Balangan', ' Kabupaten Hulu Sungai Tengah', ' Kabupaten Barito Kuala', ' Kabupaten Hulu Sungai Utara'], 'Kalimantan Tengah': ['Kabupaten Kotawaringin Timur', ' Kabupaten Barito Timur', ' Kabupaten Kotawaringin Barat', ' Kabupaten Lamandau', ' Kabupaten Gunung Mas', ' Kota Palangka Raya', ' Kabupaten Kapuas', ' Kabupaten Barito Utara', ' Kabupaten Sukamara', ' Kabupaten Murung Raya', ' Kabupaten Seruyan', ' Kabupaten Pulang Pisau', ' Kabupaten Katingan', ' Kabupaten Barito Selatan'], 'Kalimantan Timur': ['Kabupaten Kutai Kartanegara', ' Kota Samarinda', ' Kabupaten Kutai Barat', ' Kota Balikpapan', ' Kabupaten Berau', ' Kabupaten Paser', ' Kota Bontang', ' Kabupaten Kutai Timur', ' Kabupaten Penajam Paser Utara'], 'Kalimantan Utara': ['Kabupaten Tana Tidung', ' Kabupaten Nunukan', ' Kabupaten Malinau', ' Kota Tarakan', ' Kabupaten Bulungan (Bulongan)'], 'Kepulauan Riau': ['Kabupaten Karimun', ' Kota Batam', ' Kota Tanjung Pinang', ' Kabupaten Bintan', ' Kabupaten Natuna', ' Kabupaten Lingga', ' Kabupaten Kepulauan Anambas'], 'Lampung': ['Kota Bandar Lampung', ' Kabupaten Lampung Selatan', ' Kabupaten Tanggamus', ' Kabupaten Pringsewu', ' Kabupaten Lampung Tengah', ' Kabupaten Pesawaran', ' Kabupaten Tulang Bawang Barat', ' Kabupaten Pesisir Barat', ' Kabupaten Tulang Bawang', ' Kabupaten Lampung Utara', ' Kabupaten Lampung Timur', ' Kabupaten Way Kanan', ' Kota Metro', ' Kabupaten Mesuji', ' Kabupaten Lampung Barat'], 'Maluku': ['Kota Ambon', ' Kabupaten Maluku Barat Daya', ' Kabupaten Seram Bagian Timur', ' Kabupaten Seram Bagian Barat', ' Kabupaten Kepulauan Aru', ' Kota Tual', ' Kabupaten Maluku Tenggara Barat', ' Kabupaten Buru Selatan', ' Kabupaten Maluku Tenggara', ' Kabupaten Maluku Tengah', ' Kabupaten Buru'], 'Maluku Utara': ['Kabupaten Kepulauan Sula', ' Kota Ternate', ' Kabupaten Halmahera Tengah', ' Kabupaten Halmahera Utara', ' Kabupaten Halmahera Barat', ' Kota Tidore Kepulauan', ' Kabupaten Pulau Morotai', ' Kabupaten Halmahera Selatan', ' Kabupaten Halmahera Timur'], 'Nanggroe Aceh Darussalam (NAD)': ['Kota Lhokseumawe', ' Kabupaten Aceh Barat', ' Kabupaten Aceh Utara', ' Kabupaten Aceh Tamiang', ' Kabupaten Aceh Singkil', ' Kabupaten Pidie', ' Kabupaten Aceh Tengah', ' Kabupaten Aceh Selatan', ' Kabupaten Aceh Besar', ' Kabupaten Aceh Timur', ' Kabupaten Aceh Tenggara', ' Kabupaten Simeulue', ' Kota Banda Aceh', ' Kabupaten Bireuen', ' Kabupaten Bener Meriah', ' Kota Sabang', ' Kabupaten Nagan Raya', ' Kabupaten Aceh Barat Daya', ' Kota Subulussalam', ' Kota Langsa', ' Kabupaten Aceh Jaya', ' Kabupaten Gayo Lues', ' Kabupaten Pidie Jaya'], 'Nusa Tenggara Barat (NTB)': ['Kabupaten Sumbawa', ' Kabupaten Bima', ' Kota Bima', ' Kabupaten Dompu', ' Kabupaten Sumbawa Barat', ' Kabupaten Lombok Barat', ' Kota Mataram', ' Kabupaten Lombok Timur', ' Kabupaten Lombok Tengah', ' Kabupaten Lombok Utara'], 'Nusa Tenggara Timur (NTT)': ['Kota Kupang', ' Kabupaten Kupang', ' Kabupaten Sikka', ' Kabupaten Ende', ' Kabupaten Sumba Timur', ' Kabupaten Sumba Barat', ' Kabupaten Rote Ndao', ' Kabupaten Belu', ' Kabupaten Lembata', ' Kabupaten Manggarai Timur', ' Kabupaten Timor Tengah Utara', ' Kabupaten Flores Timur', ' Kabupaten Ngada', ' Kabupaten Manggarai Barat', ' Kabupaten Sumba Barat Daya', ' Kabupaten Nagekeo', ' Kabupaten Alor', ' Kabupaten Sabu Raijua', ' Kabupaten Manggarai', ' Kabupaten Sumba Tengah', ' Kabupaten Timor Tengah Selatan'], 'Papua': ['Kabupaten Mimika', ' Kota Jayapura', ' Kabupaten Jayapura', ' Kabupaten Sarmi', ' Kabupaten Biak Numfor', ' Kabupaten Boven Digoel', ' Kabupaten Jayawijaya', ' Kabupaten Mappi', ' Kabupaten Kepulauan Yapen (Yapen Waropen)', ' Kabupaten Nabire', ' Kabupaten Paniai', ' Kabupaten Merauke', ' Kabupaten Pegunungan Bintang', ' Kabupaten Asmat', ' Kabupaten Yahukimo', ' Kabupaten Waropen', ' Kabupaten Keerom', ' Kabupaten Nduga', ' Kabupaten Puncak Jaya'], 'Papua Barat': ['Kota Sorong', ' Kabupaten Sorong Selatan', ' Kabupaten Sorong', ' Kabupaten Maybrat', ' Kabupaten Teluk Bintuni', ' Kabupaten Manokwari', ' Kabupaten Fakfak', ' Kabupaten Manokwari Selatan', ' Kabupaten Teluk Wondama', ' Kabupaten Raja Ampat', ' Kabupaten Kaimana'], 'Riau': ['Kabupaten Kuantan Singingi', ' Kabupaten Rokan Hilir', ' Kota Pekanbaru', ' Kabupaten Siak', ' Kabupaten Indragiri Hulu', ' Kabupaten Kampar', ' Kota Dumai', ' Kabupaten Rokan Hulu', ' Kabupaten Pelalawan', ' Kabupaten Bengkalis', ' Kabupaten Kepulauan Meranti', ' Kabupaten Indragiri Hilir'], 'Sulawesi Barat': ['Kabupaten Mamuju', ' Kabupaten Mamuju Utara', ' Kabupaten Majene', ' Kabupaten Polewali Mandar', ' Kabupaten Mamasa'], 'Sulawesi Selatan': ['Kota Makassar', ' Kabupaten Luwu Timur', ' Kabupaten Bone', ' Kota Palopo', ' Kabupaten Maros', ' Kabupaten Pinrang', ' Kabupaten Tana Toraja', ' Kabupaten Sinjai', ' Kabupaten Gowa', ' Kabupaten Bulukumba', ' Kabupaten Soppeng', ' Kota Parepare', ' Kabupaten Toraja Utara', ' Kabupaten Pangkajene Kepulauan', ' Kabupaten Enrekang', ' Kabupaten Luwu Utara', ' Kabupaten Wajo', ' Kabupaten Selayar (Kepulauan Selayar)', ' Kabupaten Takalar', ' Kabupaten Sidenreng Rappang/Rapang', ' Kabupaten Bantaeng', ' Kabupaten Barru', ' Kabupaten Luwu', ' Kabupaten Jeneponto'], 'Sulawesi Tengah': ['Kabupaten Morowali', ' Kabupaten Banggai Kepulauan', ' Kota Palu', ' Kabupaten Banggai', ' Kabupaten Toli-Toli', ' Kabupaten Tojo Una-Una', ' Kabupaten Parigi Moutong', ' Kabupaten Poso', ' Kabupaten Sigi', ' Kabupaten Donggala', ' Kabupaten Buol'], 'Sulawesi Tenggara': ['Kabupaten Konawe', ' Kabupaten Konawe Selatan', ' Kota Kendari', ' Kabupaten Buton', ' Kabupaten Muna', ' Kabupaten Kolaka', ' Kabupaten Kolaka Utara', ' Kota Bau-Bau', ' Kabupaten Konawe Utara', ' Kabupaten Bombana', ' Kabupaten Wakatobi', ' Kabupaten Kolaka Timur', ' Kabupaten Buton Utara'], 'Sulawesi Utara': ['Kota Manado', ' Kota Tomohon', ' Kabupaten Minahasa', ' Kabupaten Minahasa Utara', ' Kabupaten Minahasa Selatan', ' Kabupaten Bolaang Mongondow Selatan', ' Kota Bitung', ' Kabupaten Bolaang Mongondow Timur', ' Kabupaten Minahasa Tenggara', ' Kabupaten Kepulauan Sangihe', ' Kota Kotamobagu', ' Kabupaten Kepulauan Talaud', ' Kabupaten Bolaang Mongondow (Bolmong)', ' Kabupaten Kepulauan Siau Tagulandang Biaro (Sitaro)', ' Kabupaten Bolaang Mongondow Utara'], 'Sumatera Barat': ['Kabupaten Dharmasraya', ' Kota Solok', ' Kabupaten Agam', ' Kota Bukittinggi', ' Kabupaten Pasaman Barat', ' Kota Padang', ' Kabupaten Padang Pariaman', ' Kabupaten Sijunjung (Sawah Lunto Sijunjung)', ' Kota Payakumbuh', ' Kabupaten Lima Puluh Koto/Kota', ' Kabupaten Solok', ' Kabupaten Solok Selatan', ' Kabupaten Tanah Datar', ' Kabupaten Kepulauan Mentawai', ' Kabupaten Pesisir Selatan', ' Kabupaten Pasaman', ' Kota Pariaman', ' Kota Padang Panjang', ' Kota Sawah Lunto'], 'Sumatera Selatan': ['Kabupaten Lahat', ' Kota Palembang', ' Kota Lubuk Linggau', ' Kabupaten Banyuasin', ' Kabupaten Musi Banyuasin', ' Kabupaten Ogan Komering Ilir', ' Kabupaten Ogan Komering Ulu Selatan', ' Kabupaten Empat Lawang', ' Kota Pagar Alam', ' Kabupaten Ogan Komering Ulu Timur', ' Kabupaten Ogan Komering Ulu', ' Kabupaten Muara Enim', ' Kabupaten Musi Rawas', ' Kota Prabumulih', ' Kabupaten Ogan Ilir'], 'Sumatera Utara': ['Kota Medan', ' Kabupaten Batu Bara', ' Kabupaten Deli Serdang', ' Kabupaten Labuhan Batu Utara', ' Kabupaten Labuhan Batu', ' Kabupaten Simalungun', ' Kabupaten Mandailing Natal', ' Kabupaten Tapanuli Tengah', ' Kabupaten Langkat', ' Kabupaten Tapanuli Utara', ' Kota Binjai', ' Kabupaten Humbang Hasundutan', ' Kabupaten Labuhan Batu Selatan', ' Kabupaten Serdang Bedagai', ' Kota Sibolga', ' Kabupaten Karo', ' Kabupaten Nias Selatan', ' Kabupaten Asahan', ' Kabupaten Toba Samosir', ' Kabupaten Dairi', ' Kota Padang Sidempuan', ' Kota Gunungsitoli', ' Kota Pematang Siantar', ' Kabupaten Nias Utara', ' Kabupaten Nias Barat', ' Kabupaten Tapanuli Selatan', ' Kabupaten Padang Lawas Utara', ' Kota Tebing Tinggi', ' Kabupaten Samosir', ' Kabupaten Padang Lawas', ' Kabupaten Nias', ' Kota Tanjung Balai', ' Kabupaten Pakpak Bharat']}
    
    
    

if __name__ == "__main__":
    app.run(debug=True, port=5000)