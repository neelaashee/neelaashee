from googleapiclient.discovery import build 
import pymongo
import psycopg2
import pandas as pd
import streamlit as st

def Api_connect():
    Api_Id = "AIzaSyDIemuKImj8b1Zy3yXIhq6AkcygQnNLm90"
    api_service_name="youtube"
    api_version="v3"
    youtube=build(api_service_name,api_version,developerKey=Api_Id)
    return youtube
youtube=Api_connect()


def get_channel_info(channel_id):
    request=youtube.channels().list(
                    part="snippet,contentDetails,statistics",
                    id=channel_id
    )
    response=request.execute()
    for i in response['items']:
        data=dict(channel_Name=i["snippet"]["title"],
                channel_Id=i["id"],
                subscribers=i["statistics"]["subscriberCount"],
                views=i["statistics"]["videoCount"],
                Total_videos=i["statistics"]["videoCount"],
                channel_Description=i["snippet"]["description"],
                Playlist_Id=i["contentDetails"]["relatedPlaylists"]["uploads"])
    return data


def get_video_ids(channel_Id):
    video_ids=[]
    response=youtube.channels().list(id=channel_Id,part="contentDetails").execute()
    Playlist_Id=response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    next_page_token=None
    while True:

        response1=youtube.playlistItems().list(
                                            part="snippet",
                                            playlistId=Playlist_Id,maxResults=50,pageToken=next_page_token).execute()
        for i in range(len(response1["items"])):
            video_ids.append(response1["items"][i]["snippet"]["resourceId"]["videoId"])
        next_page_token=response1.get("nextPageToken") 
        if next_page_token is None:
           break 
    return video_ids  


def get_video_info(video_ids):
    video_data=[]
    for video_id in video_ids:
        request=youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
        )
        response=request.execute()

        for item in response["items"]:
            data=dict(channel_Name=item["snippet"]["channelTitle"],
                     channel_Id=item["snippet"]["channelId"],
                     video_Id=item["id"],
                     Title=item["snippet"]["title"],
                     Tags=item["snippet"].get("tags"),
                     Thumbnail=item["snippet"]["thumbnails"]["default"]["url"],
                     Description=item["snippet"].get("description"),
                     Published_Date=item["snippet"]["publishedAt"],
                     Duration=item["contentDetails"]["duration"],
                     Views=item["statistics"].get("viewCount"),
                     Likes=item["statistics"].get("likeCount"),
                     Comments=item["statistics"].get("commentCount"),
                     Favorite_Count=item["statistics"]["favoriteCount"],
                     Definition=item["contentDetails"]["definition"],
                     Caption_Status=item["contentDetails"]["caption"]

                    )
            video_data.append(data)
    return video_data


def get_comment_info(video_ids):
    Comment_data=[]
    try:
        for video_id in video_ids:
            request=youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=50
                )
            response=request.execute()

            for item in response["items"]:
                data=dict(Comment_Id=item["snippet"]["topLevelComment"]["id"],
                        video_Id=item["snippet"]["topLevelComment"]["snippet"]["videoId"],
                        Comment_Text=item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                        Comment_Author=item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                        Comment_Published=item["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
                        )
            Comment_data.append(data)


    except:
        pass
    return Comment_data  


client=pymongo.MongoClient("mongodb+srv://neelaashee:naren1286@cluster0.81fvicq.mongodb.net/?retryWrites=true&w=majority")


def channel_details(channel_id):
     ch_details=get_channel_info(channel_id)
     vi_ids=get_video_ids(channel_id)
     vi_details=get_video_info(vi_ids)
     com_details=get_comment_info(vi_ids)

     collection1=db["channel_details"]
     collection1.insert_one({"channel_information":ch_details,
                             "video_information":vi_details,
                             "comment_information": com_details})
     return "upload completed"


def channels_table():
    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="naren1286",
                        database="youtube_data",
                        port="5432")
    cursor=mydb.cursor()

    drop_query='''drop table if exists channels'''
    cursor.execute(drop_query)
    mydb.commit()



    try:
        create_query='''create table if not exists channels(channel_Name varchar(100),
                                                            channel_Id varchar(80)primary key,
                                                            subscribers bigint,
                                                            views bigint,
                                                            Total_videos int,
                                                            channel_Description text,
                                                            Playlist_Id varchar(80))'''
        cursor.execute(create_query)
        mydb.commit()
    except :
        print("table created") 

    ch_list=[]
    db=client["youtube_data"]
    collection1=db["channel_details"]
    for ch_data in collection1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=pd.DataFrame(ch_list)

    for index,row in df.iterrows():
        insert_query='''insert into  channels(channel_Name ,
                                                channel_Id,
                                                subscribers,
                                                views,
                                                Total_videos,
                                                channel_Description,
                                                Playlist_Id)
                                                values(%s,%s,%s,%s,%s,%s,%s)'''
        values=(row["channel_Name"],
                row["channel_Id"],
                row["subscribers"],
                row["views"],
                row["Total_videos"],
                row["channel_Description"],
                row["Playlist_Id"])
        
        
        cursor.execute( insert_query,values)
        mydb.commit()


def videos_table():
    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="naren1286",
                        database="youtube_data",
                        port="5432")
    cursor=mydb.cursor()

    drop_query='''drop table if exists videos'''
    cursor.execute(drop_query)
    mydb.commit()



    create_query='''create table if not exists videos(channel_Name varchar(100),
                                                    channel_Id varchar(100),
                                                    video_Id varchar(30) primary key,
                                                    Title varchar(150),
                                                    Tags text,
                                                    Thumbnail varchar(200),
                                                    Description text,
                                                    Published_Date timestamp,
                                                    Duration interval,
                                                    Views bigint,
                                                    Likes bigint,
                                                    Comments int,
                                                    Favorite_Count int,
                                                    Definition varchar(10),
                                                    Caption_Status varchar(50))'''
    cursor.execute(create_query)
    mydb.commit()

    vi_list=[]
    db=client["youtube_data"]
    collection1=db["channel_details"]
    for vi_data in collection1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    df1=pd.DataFrame(vi_list)

    for index,row in df1.iterrows():
            insert_query='''insert into  videos(channel_Name,
                                                channel_Id,
                                                video_Id,
                                                Title,
                                                Tags,
                                                Thumbnail,
                                                Description,
                                                Published_Date,
                                                Duration,
                                                Views,
                                                Likes,
                                                Comments,
                                                Favorite_Count,
                                                Definition,
                                                Caption_Status)
                                                    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
            values=(row["channel_Name"],
                    row["channel_Id"],
                    row["video_Id"],
                    row["Title"],
                    row["Tags"],
                    row["Thumbnail"],
                    row["Description"],
                    row["Published_Date"],
                    row["Duration"],
                    row["Views"],
                    row["Likes"],
                    row["Comments"],
                    row["Favorite_Count"],
                    row["Definition"],
                    row["Caption_Status"])
                    
            
            
            cursor.execute( insert_query,values)
            mydb.commit()


def comment_table():
    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="naren1286",
                        database="youtube_data",
                        port="5432")
    cursor=mydb.cursor()

    drop_query='''drop table if exists comments'''
    cursor.execute(drop_query)
    mydb.commit()



    create_query='''create table if not exists comments(Comment_Id varchar(100)primary key,
                                                        video_Id varchar(50),
                                                        Comment_Text text,
                                                        Comment_Author varchar(150),
                                                        Comment_Published timestamp)'''
    cursor.execute(create_query)
    mydb.commit()

    com_list=[]
    db=client["youtube_data"]
    collection1=db["channel_details"]
    for com_data in collection1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df2=pd.DataFrame(com_list)

    for index,row in df2.iterrows():
            insert_query='''insert into  comments(Comment_Id,
                                                video_Id,
                                                Comment_Text,
                                                Comment_Author,
                                                Comment_Published)
                                                values(%s,%s,%s,%s,%s)'''
            values=(row["Comment_Id"],
                    row["video_Id"],
                    row["Comment_Text"],
                    row["Comment_Author"],
                    row["Comment_Published"])
                    
                    
            
            
            cursor.execute( insert_query,values)
            mydb.commit()


def tables():
    channels_table()
    videos_table()
    comment_table()

    return"tables created"


def show_channels_table():
    ch_list=[]
    db=client["youtube_data"]
    collection1=db["channel_details"]
    for ch_data in collection1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=st.dataframe(ch_list)

    return df


def show_videos_table():
    vi_list=[]
    db=client["youtube_data"]
    collection1=db["channel_details"]
    for vi_data in collection1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    df1=st.dataframe(vi_list)

    return df1


def show_comment_table():
    com_list=[]
    db=client["youtube_data"]
    collection1=db["channel_details"]
    for com_data in collection1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df2=st.dataframe(com_list)

    return df2


with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("skill Take Away")
    st.caption("Python Scripting")
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption("Data Management Using MongoDB And SQL")

    channel_id=st.text_input("Enter the channel ID")

    if st.button("collect and store data"):
        ch_ids=[]
        db=client["youtube_data"]
        collection1=db["channel_details"]
        for ch_data in collection1.find({},{"_id":0,"channel_information":1}):
            ch_ids.append(ch_data["channel_information"]["channel_Id"])

        if channel_id in ch_ids:
            st.success("channel details of the given channel id already exsists")

        else:
            insert=channel_details(channel_id)
            st.success(insert)

    if st.button("migrate to sql"):
        Table=tables()  
        st.success(Table) 

    show_table=st.radio("SELECT THE TABLES FOR VIEW",("CHANNELS","VIDEOS","COMMENTS")) 
    if show_table=="CHANNELS":
        show_channels_table()

    elif show_table=="VIDEOS":
        show_videos_table() 

    elif show_table=="COMMENTS":
        show_comment_table()    




mydb=psycopg2.connect(host="localhost",
                    user="postgres",
                    password="naren1286",
                    database="youtube_data",
                    port="5432")
cursor=mydb.cursor()

question=st.selectbox("select your question",("1.All the videos and the channel name",
                                              "2.Channels with most number of videos",
                                              "3.10 most viewed videos",
                                              "4.comments in each videos",
                                              "5.Videos with highest likes",
                                              "6.Likes of all videos",
                                              "7.views of each channel",
                                              "8.videos published in the year of 2022",
                                              "9.average duration of all videos in each channel",
                                              "10.videos with highest number of comments"))

if question=="1.All the videos and the channel name":
    query1='''select title as videos,channel_name as channelname from videos'''
    cursor.execute(query1)
    mydb.commit()
    t1=cursor.fetchall()
    df=pd.DataFrame(t1,columns=["video title","channel name"])
    st.write(df)

elif question=="2.Channels with most number of videos":
    query2='''select channel_name as channelname,total_videos as no_videos from channels
                order by total_videos desc'''
    cursor.execute(query2)
    mydb.commit()
    t2=cursor.fetchall()
    df2=pd.DataFrame(t2,columns=["channel name","No of videos"])
    st.write(df2)  

elif question=="3.10 most viewed videos":
    query3='''select views as views,channel_name as channelname,title as videotitle from videos
                where views is not null order by views desc limit 10'''
    cursor.execute(query3)
    mydb.commit()
    t3=cursor.fetchall()
    df3=pd.DataFrame(t3,columns=["views","channelname","videotitle"])
    st.write(df3)

elif question=="4.comments in each videos":
    query4='''select comments as comments,title as videotitle from videos
                where comments is not null'''
    cursor.execute(query4)
    mydb.commit()
    t4=cursor.fetchall()
    df4=pd.DataFrame(t4,columns=["comments","videotitle"])
    st.write(df4)

elif question=="5.Videos with highest likes":
    query5='''select title as videotitle,channel_name as channelname,likes as likecount from videos
                where likes is not null order by likes desc'''
    cursor.execute(query5)
    mydb.commit()
    t5=cursor.fetchall()
    df5=pd.DataFrame(t5,columns=["videotitle","channelname","likecount"])
    st.write(df5)

elif question=="6.Likes of all videos":
    query6='''select likes as likecount,title as videotitle from videos'''
    cursor.execute(query6)
    mydb.commit()
    t6=cursor.fetchall()
    df6=pd.DataFrame(t6,columns=["likecount","videotitle"])
    st.write(df6)

elif question=="7.views of each channel":
    query7='''select channel_name as channelname,views as totalviews from channels'''
    cursor.execute(query7)
    mydb.commit()
    t7=cursor.fetchall()
    df7=pd.DataFrame(t7,columns=["channelname","totalviews"])
    st.write(df7)

elif question=="8.videos published in the year of 2022":
    query8='''select title as videotitle,published_date as video_release_date,channel_name as channelname from videos
                where extract (year from published_date)=2022'''
    cursor.execute(query8)
    mydb.commit()
    t8=cursor.fetchall()
    df8=pd.DataFrame(t8,columns=["videotitle","published_date","channelname"])
    st.write(df8)

elif question== "9.average duration of all videos in each channel":
    query9='''select channel_name as channelname,AVG(duration) as averageduration from videos
                group by channel_name'''
    cursor.execute(query9)
    mydb.commit()
    t9=cursor.fetchall()
    df9=pd.DataFrame(t9,columns=["channelname","averageduration"])
    df9
    
    T9=[]
    for index,row in df9.iterrows():
        channel_title=row["channelname"]
        average_duration=row["averageduration"]
        average_duration_str=str("averageduration")
        T9.append(dict(channeltitle=channel_title,avgduration=average_duration_str))
        df1=pd.DataFrame(T9)
        st.write(df1)

elif question== "10.videos with highest number of comments":
    query10='''select title as videotitle,channel_name as channelname,comments as comments from videos
                where comments is not null order by comments desc'''
    cursor.execute(query10)
    mydb.commit()
    t10=cursor.fetchall()
    df10=pd.DataFrame(t10,columns=["videotitle","channelname","comments"])
    st.write(df10)







    
           
    





