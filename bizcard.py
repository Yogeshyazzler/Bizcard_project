import streamlit as st
from streamlit_option_menu import option_menu
import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import sqlite3

def imagetotxt(path):
  input_img = Image.open(path)
  image_array=np.array(input_img)
  reader=easyocr.Reader(['en'])
  text=reader.readtext(image_array,detail=0)
  return text,input_img

def extracted_text(text_image):

  extracted_dict = {"NAME":[], "DESIGNATION":[],"COMPANY_NAME":[],"CONTACT_NUMBER":[],"EMAIL":[],
                    "WEBSITE":[],"ADDRESS":[],"STATE":[],"PINCODE":[]}
  indian_states = [ "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
                    "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
                      "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
                      "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                      "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh",
                      "Uttarakhand", "West Bengal", "Andaman and Nicobar Islands", "Chandigarh",
                      "Dadra and Nagar Haveli and Daman and Diu",
                    "Lakshadweep", "Delhi", "Puducherry", "Ladakh", "Jammu and Kashmir" ]

  indian_states_no_spaces = [state.replace(" ", "") for state in indian_states]
  unique_pincodes = set()

  extracted_dict["NAME"].append(text_image[0])
  extracted_dict["DESIGNATION"].append(text_image[1])

  for i in range (2,len(text_image)):
    if text_image[i].startswith("+") or (text_image[i].replace("-","").isdigit() and '-' in text_image[i]):
      extracted_dict["CONTACT_NUMBER"].append(text_image[i])

    elif "@" in text_image[i] and ".com" in text_image[i]:
      extracted_dict["EMAIL"].append(text_image[i])

    elif "WWW" in text_image[i] or "www" in text_image[i] or "Www" in text_image[i] or "wWw" in text_image[i] or "wwW" in text_image[i] or re.search(r'\.com$',text_image[i]) :
      small=text_image[i].lower()
      extracted_dict["WEBSITE"].append(small)

    elif text_image[i].strip() in indian_states or text_image[i].strip() in indian_states_no_spaces or text_image[i].split()[0] in indian_states or text_image[i].split()[0] in indian_states_no_spaces:
      extracted_dict["STATE"].append(text_image[i].split()[0])
      extracted_dict["PINCODE"].append(text_image[i].split()[1])

    elif re.match(r'^[A-Za-z\s]+$', text_image[i]):
        extracted_dict["COMPANY_NAME"].append(text_image[i])

    else:
      remove_colon=re.sub(r'[,;]',"",text_image[i])
      if "TamilNadu" in text_image[i]:
        if "TamilNadu" in text_image[i] or "Tamil Nadu" in text_image[i]:
          extracted_dict["STATE"].append("Tamil Nadu")
        for i in range(len(text_image)):
          match = re.search(r'\d{6}', text_image[i])
          if match:
            six_digit_number = match.group(0)
            unique_pincodes.add(six_digit_number)
        extracted_dict["PINCODE"] = list(unique_pincodes)

        extracted_dict["ADDRESS"].append(remove_colon)

        updated_addresses = []
        for address in extracted_dict["ADDRESS"]:
          if "TamilNadu" in address:
            updated_address = address.replace("TamilNadu", "")
          if extracted_dict["PINCODE"] in extracted_dict["ADDRESS"]:
            updated_address = updated_address.replace(*extracted_dict["PINCODE"], "")
            updated_address = ' '.join(address.split())

        updated_addresses.append(updated_address)

        combined_address = ' '.join(updated_addresses)

        extracted_dict["ADDRESS"] = [combined_address]
      else:
        extracted_dict["ADDRESS"].append(remove_colon)

  return extracted_dict


def extracted_info(raw_extract):
  for key in raw_extract:
    raw_extract[key]=['  '.join(raw_extract[key])]
  return raw_extract

#streamlit part
st.set_page_config(layout="wide")
st.title("EXTRACTING BUSINESS CARD DATA WITH OCR")

with st.sidebar:

  select = option_menu("Main Menu",["Home","Upload & Modify", "Delete"])

if select == "Home":
  st.wirte("EasyOCR is a Python computer language Optical Character Recognition (OCR) module that is both flexible and easy to use. OCR technology is useful for a variety of tasks, including data entry automation and image analysis.")
  st.write("It enables computers to identify and extract text from photographs or scanned documents.")
  st.write(" ")

elif select == "Upload & Modify":
  img=st.file_uploader("upload Image",type=["png","jpg","jpeg"])

  if img is not None:
    st.image(img, width=300)

    text_image, input_image = imagetotxt(img)

    text_dict = extracted_text(text_image)

    final_dict = extracted_info(text_dict)

    if final_dict:
      st.success("Data Extracted")

    df=pd.DataFrame(final_dict)

#converting image to bytes

    img_bytes=io.BytesIO()
    input_image.save(img_bytes,format='PNG')

    image_data = img_bytes.getvalue()

    #creating a dictionary

    data = {"Image":[image_data]}

    df1=pd.DataFrame(data)

    concat_df=pd.concat([df1,df],axis=1)

    st.dataframe(concat_df)

    button1=st.button("Save",use_container_width=True)

    if button1:
      mydb=sqlite3.connect("bizcard.db")
      cursor=mydb.cursor()

      #table creation

      create_query = '''create table if not exists bizcardx(image text,name varchar(255),
                        designation varchar(255),company_name varchar(255),contact_number varchar(255),
                        email varchar(255),website varchar(255),address text,state varchar(255),
                        pincode varchar(255))'''
      cursor.execute(create_query)
      mydb.commit()

      Insert_query = '''insert into bizcardx(image,name,designation,company_name,contact_number,
                        email,website,address,state,pincode) values (?,?,?,?,?,?,?,?,?,?)'''

      datas=concat_df.values.tolist()[0]
      cursor.execute(Insert_query,datas)
      mydb.commit()
      st.success("Data Saved")

  method = st.radio("select the method",["None","Preview data","Modify data"])

  if method== "None":
    st.write("")

  if method=="Preview data":
    mydb=sqlite3.connect("bizcard.db")
    cursor=mydb.cursor()

    select_query='''select * from bizcardx;'''
    cursor.execute(select_query)
    result=cursor.fetchall()
    mydb.commit()

    table_df = pd.DataFrame(result,columns=("Image Data","Name","Designation","Company_Name","Contact","Email","Website","Address","State","Pincode"))
    st.dataframe(table_df)

  elif method=="Modify data":
    mydb=sqlite3.connect("bizcard.db")
    cursor=mydb.cursor()

    select_query='''select * from bizcardx;'''
    cursor.execute(select_query)
    result=cursor.fetchall()
    mydb.commit()

    table_df = pd.DataFrame(result,columns=("Image Data","Name","Designation","Company_Name","Contact","Email","Website","Address","State","Pincode"))

    col1,col2=st.columns(2)

    with col1:
      selected_name = st.selectbox("Select the Name",table_df["Name"])

    df3=table_df[table_df["Name"]==selected_name]


    df4=df3.copy()

    col1,col2=st.columns(2)

    with col1:
      new_Image_Data=st.text_input("Image Data",df3["Image Data"].unique()[0])
      new_name=st.text_input("Name",df3["Name"].unique()[0])
      new_designation=st.text_input("Designation",df3["Designation"].unique()[0])
      new_Company_Name=st.text_input("Company_Name",df3["Company_Name"].unique()[0])
      new_Contact=st.text_input("Contact",df3["Contact"].unique()[0])

      df4["new_Image_Data"]=new_Image_Data
      df4["Name"]=new_name
      df4["new_designation"]=new_designation
      df4["new_Company_Name"]=new_Company_Name
      df4["new_Contact"]=new_Contact


    with col2:
      new_Email=st.text_input("Email",df3["Email"].unique()[0])
      new_Website=st.text_input("Website",df3["Website"].unique()[0])
      new_Address=st.text_input("Address",df3["Address"].unique()[0])
      new_State=st.text_input("State",df3["State"].unique()[0])
      new_Pincode=st.text_input("Pincode",df3["Pincode"].unique()[0])

      df4["new_Email"]=new_Email
      df4["Website"]=new_Website
      df4["new_Address"]=new_Address
      df4["new_State"]=new_State
      df4["new_Pincode"]=new_Pincode


    st.dataframe(df4)

    col1,col2 = st.columns(2)

    with col1:
      button3=st.button("Modify",use_container_width=True)
    if button3:
       mydb=sqlite3.connect("bizcard.db")
       cursor=mydb.cursor()
       cursor.execute(f"delete from bizcardx where Name = '{selected_name}'")
       mydb.commit()

       Insert_query = '''insert into bizcardx(image,name,designation,company_name,contact_number,
                        email,website,address,state,pincode) values (?,?,?,?,?,?,?,?,?,?)'''

       datas=df4.values.tolist()[0]
       cursor.execute(Insert_query,datas)
       mydb.commit()
       st.success("Data Modified")

elif select == "Delete":
  mydb=sqlite3.connect("bizcard.db")
  cursor=mydb.cursor()

  col1,col2=st.columns(2)

  with col1:
    mydb=sqlite3.connect("bizcard.db")
    cursor=mydb.cursor()

    select_query = 'select name from bizcardx'
    cursor.execute(select_query)
    result=cursor.fetchall()
    mydb.commit()

    names=[]

    for i in result:
      names.append(i[0])

    selected_name = st.selectbox("Select the Name",names)

  with col2:
    mydb=sqlite3.connect("bizcard.db")
    cursor=mydb.cursor()

    select_query = f"select designation from bizcardx where name = '{selected_name}'"
    cursor.execute(select_query)
    result2=cursor.fetchall()
    mydb.commit()

    designation=[]
    for j in result2:
      designation.append(j[0])

    selected_designation = st.selectbox("Select the designation",designation)

  if selected_name and selected_designation:
    col1,col2,col3=st.columns(3)

    with col1:
      st.write("")
      st.write("")
      st.write(f"selected name is {selected_name}")
      st.write(f"selected designation is {selected_designation}")
      st.write("")
      st.write("")
      remove=st.button("Remove",use_container_width=True)

      if remove:
        cursor.execute(f"delete from bizcardx where Name = '{selected_name}' and designation='{selected_designation}'")
        mydb.commit()
        st.success("Data Deleted")


