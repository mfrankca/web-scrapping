
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import os
import boto3
from io import BytesIO
import base64
#from utility_functions import get_base64_of_bin_file, build_markup_for_logo, add_logo

#load logo file
def get_base64_of_bin_file(png_file):
    with open(png_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

def build_markup_for_logo(
    png_file,
    background_position="50% 10%",
    margin_top="10%",
    image_width="60%",
    image_height="",
):
    binary_string = get_base64_of_bin_file(png_file)
    return """
            <style>
                [data-testid="stSidebarNav"] {
                    background-image: url("data:image/png;base64,%s");
                    background-repeat: no-repeat;
                    background-position: %s;
                    margin-top: %s;
                    background-size: %s %s;
                }
            </style>
            """ % (
        binary_string,
        background_position,
        margin_top,
        image_width,
        image_height,
    )
            
def add_logo(png_file):
    logo_markup = build_markup_for_logo(png_file)
    st.markdown(
        logo_markup,
        unsafe_allow_html=True,
    )  
    
def display_sidebar():
    """
    Display the sidebar with a logo image and documentation.
    """
    image_path = "uploads/logo.png"
    st.sidebar.image(image_path, use_column_width=True)

    with st.sidebar.expander("Documentation", icon="📚"):
       st.write("""
        **Welcome to the SunRayCity Management Tool**

        ### About SunRayCity Sunglasses
        At SunRayCity Sunglasses, we search the world for the best deals on fashion and sport sunglasses. We only sell authentic and brand name sunglasses. If you are searching for a specific model that you cannot find on the site, send us an email at [sales@sunraycity.com](mailto:sales@sunraycity.com) and we will do our best to find it. We operate online only to offer these deals.

        ### Features
        - **Manage Customers**: Keep track of customer details and interactions.
        - **Product Catalog Management**: Maintain and update the product catalog.
        - **eBay Product Catalog Scraping**: Scrape product data from eBay.
        - **Scrape eBay Reviews**: Scrape reviews from the following eBay feedback pages:
          - [SunRayCity eBay Store 1](https://www.ebay.com/fdbk/feedback_profile/sunraycity)
          - [SunRayCity eBay Store 2](https://www.ebay.com/fdbk/feedback_profile/sunraycity_store)
        - **Compare Product Catalogs**: Compare the product catalog on eBay vs. the SunRayCity website.

        ### Instructions
        1. **Choose Site**: Select which eBay feedback site to scrape.
        2. **Enter URL**: Provide the URL of the eBay feedback page.
        3. **Scrape Data**: Click "Scrape Data" to collect and save reviews.

        Supported feedback sites: **eBay Feedback Site 1**, **eBay Feedback Site 2**.
        """)
           
def scrape_ebay(item):
    url = f'https://www.ebay.com/itm/{item}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    row = {'Listing ID': item}
    try:
         title_element = soup.find('h1', attrs={'class': 'x-item-title__mainTitle'})
         row['Title'] = title_element.text.replace('Details about', '').strip() if title_element else 'Not Available'
    except AttributeError:
          row['Title'] = 'Not Available' 
    try:     
        # Find the div with the class 'x-sellercard-atf__info__about-seller'
        seller_div = soup.find('div', class_='x-sellercard-atf__info__about-seller')

        # Find the span with the class 'ux-textspans ux-textspans--BOLD' inside the div
        seller_span = seller_div.find('span', class_='ux-textspans ux-textspans--BOLD')

        # Extract the seller name from the span
        seller_name = seller_span.text.strip()   
    except AttributeError:
        seller_name ='Not Available'
    row['Seller'] = seller_name

    try:
      #price = soup.find('div', attrs={'class': 'x-price-primary'}).find('span').text.split('$')[-1].strip()
      price = soup.find('div', attrs={'class': 'x-price-primary'}).find('span').text.strip()
    except AttributeError:
            price = 'Not Available'
    row['Price'] = price

    try:
    # Locate the quantity element by its class and ID
     qty_element = soup.find('div', attrs={'class': 'x-quantity__availability', 'id': 'qtyAvailability'})
     if qty_element:
        # Extract the text from the span inside the div
        qty_text = qty_element.find('span', class_='ux-textspans ux-textspans--SECONDARY').text.strip()
     

        # Determine the quantity based on the text content
        if 'Last One' in qty_text:
            row['Quantity'] = '1'
        elif 'Out of Stock' in qty_text:
            row['Quantity'] = '0'
        elif 'More than' in qty_text:
            # Extract the number after "More than"
            row['Quantity'] = qty_text.split('More than')[-1].split()[0].strip()
        elif 'available' in qty_text:
            # Extract the number directly from "X available"
            row['Quantity'] = qty_text.split('available')[0].strip()
        else:
            # Default case: try extracting numeric value from unexpected formats
            row['Quantity'] = ''.join(filter(str.isdigit, qty_text))  # Extract digits

        #st.write(f"Parsed quantity: {row['Quantity']}")  # Output the parsed quantity for debugging
     else:
        row['Quantity'] = '1'  # Default if no element is found
    except Exception as e:
      row['Quantity'] = 'Not Available'
      st.write(f"Error occurred quantity: {e}")  # Log the error for debugging


    
    # Get images
    try:
          img_container = soup.find('div', {'class': 'ux-image-carousel-container'})
          if img_container:
           img_urls = [img.get('data-zoom-src', '') for img in img_container.find_all('img')[:3]]
          else:
           img_urls = []
    except Exception as e:
          print(f"An error occurred while retrieving image URLs: {e}")
          img_urls = []

     # Handle cases where fewer than 3 images are available
    row['Image URL 1'] = img_urls[0] if len(img_urls) > 0 else ''
    row['Image URL 2'] = img_urls[1] if len(img_urls) > 1 else ''
    row['Image URL 3'] = img_urls[2] if len(img_urls) > 2 else ''
             
    # Extract information from the first table
    try:
          table = soup.find('div', attrs={'id': 'viTabs_0_is'})
          if table:
             labels = table.findAll('div', {'class': 'ux-labels-values__labels-content'})
             values = table.findAll('div', {'class': 'ux-labels-values__values-content'})
             for nth, label in enumerate(labels):
                row[label.getText()] = values[nth].getText()
          else:
                print("Table 1 not found.")
    except:pass
    
    #Exception as e:
     #      print(f"An error occurred while extracting information from Table 1: {e}")

        # Extract information from the second table
    try:
           table1 = soup.find('div', attrs={'class': 'ux-layout-section-module'})
           if table1:
              labels = table1.findAll('div', {'class': 'ux-labels-values__labels-content'})
              values = table1.findAll('div', {'class': 'ux-labels-values__values-content'})
              for nth, label in enumerate(labels):
                 row[label.getText()] = values[nth].getText()
           else:
             print("Table 2 not found.")
    except Exception as e:
              print(f"An error occurred while extracting information from Table 2: {e}")

    return row
    # Example of data extraction
    ####title = soup.find('h1', {'class': 'it-ttl'}).text.strip() if soup.find('h1', {'class': 'it-ttl'}) else "N/A"
    ###price = soup.find('span', {'class': 'notranslate'}).text.strip() if soup.find('span', {'class': 'notranslate'}) else "N/A"
    
    return {
        'listing_id': item,
        'title': title,
        'price': price,
        'Seller':seller_name,
        'Quantity' :qty
    }

def perform_web_scraping(input_filepath):
    # Determine the file type and read the data accordingly
    _, file_extension = os.path.splitext(input_filepath)
    
    if file_extension == '.csv':
        listings = pd.read_csv(input_filepath)
    elif file_extension == '.txt':
        listings = pd.read_csv(input_filepath, header=None, names=['item'])
    else:
        st.error("Unsupported file type. Please upload a CSV or TXT file.")
        return []

    data = []
    for item in listings['item']:
        item_data = scrape_ebay(item)
        data.append(item_data)

    return data

def generate_output_files(data, output_format):
    output_files = []
    df = pd.DataFrame(data)
    
    # Define the desired columns order
    columns_order = [
        'Listing ID', 'Title', 'Type', 'Seller', 'Price', 'Quantity', 'Image URL 1', 'Image URL 2', 'Image URL 3', 
        'Brand', 'Model', 'MPN', 'Frame Color', 'Frame Material', 'Style', 'Features', 'Lens Color', 'Lens Technology',
        'Lens Material', 'Department',  
        'Lens Socket Width', 'Eye', 'Bridge Width', 'Bridge', 'Vertical', 'Temple Length', 
        'Country/Region of Manufacture', 'UPC'
    ]

    # Ensure all columns are present in the DataFrame, create missing columns with empty values
    for column in columns_order:
        if column not in df.columns:
            df[column] = ""
  
    # Update 'Lens Socket Width' with 'Eye' if 'Lens Socket Width' is empty or None, and 'Eye' is not empty
    df['Lens Socket Width'] = df.apply(
    lambda row: row['Eye'] if (pd.isna(row['Lens Socket Width']) or row['Lens Socket Width'].strip() == '')  else row['Lens Socket Width'], axis=1
)

    # Update 'Bridge Width' with 'Bridge' if 'Bridge Width' is empty or None, and 'Bridge' is not empty
    df['Bridge Width'] = df.apply(
    lambda row: row['Bridge'] if (pd.isna(row['Bridge Width']) or row['Bridge Width'].strip() == '')  else row['Bridge Width'], axis=1
)
    columns_order = [
        'Listing ID', 'Title', 'Type', 'Seller', 'Price', 'Quantity', 'Image URL 1', 'Image URL 2', 'Image URL 3', 
        'Brand', 'Model', 'MPN', 'Frame Color', 'Frame Material', 'Style', 'Features', 'Lens Color', 'Lens Technology',
        'Lens Material', 'Department',  
        'Lens Socket Width', 'Bridge Width',  'Vertical', 'Temple Length', 
        'Country/Region of Manufacture', 'UPC'
    ]

    # Reorder the columns as per the desired order
    filtered_df = df[columns_order]

    # Generate the output files in the selected format(s)
    if 'Excel' in output_format:
        excel_file = 'output.xlsx'
        filtered_df.to_excel(excel_file, index=False)
        output_files.append(excel_file)
        
    if 'JSON' in output_format:
        json_file = 'output.json'
        filtered_df.to_json(json_file, orient='records')
        output_files.append(json_file)
        
    if 'CSV' in output_format:
        csv_file = 'output.csv'
        filtered_df.to_csv(csv_file, index=False)
        output_files.append(csv_file)

    return output_files


#image_path = "uploads//logo.png"
#st.sidebar.image(image_path, use_column_width=True)
#st.title("Welcome to SunRayCity Management")  

st.title('Web Scraping App')
st.write('Upload a file with listing numbers and select the output file format.')
display_sidebar()
uploaded_file = st.file_uploader('Choose a file', type=['csv', 'txt'])
output_format = st.multiselect('Select output format', ['Excel', 'JSON', 'CSV'])

if uploaded_file is not None:
    if st.button('Scrape Data'):
        # Save uploaded file temporarily
        input_filepath = os.path.join('temp', uploaded_file.name)
        with open(input_filepath, 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # Perform web scraping
        data = perform_web_scraping(input_filepath)

        if data:
            # Generate output files
            output_files = generate_output_files(data, output_format)

            st.success('Scraping and file generation completed successfully!')

            for file in output_files:
                with open(file, 'rb') as f:
                    btn = st.download_button(
                        label=f"Download {file}",
                        data=f,
                        file_name=file,
                        mime='application/octet-stream'
                    )

if not os.path.exists('temp'):
    os.makedirs('temp')
