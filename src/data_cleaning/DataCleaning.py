from .ApartmentsDataFrame import ApartmentsDataFrame
from ..utils.helpers import get_usd_exchange_rate
import pandas as pd
from datetime import datetime
import re



class DataCleaning:
    def __init__(self):
        self.apartments_df = ApartmentsDataFrame().get_df()
        self.currency_rate = get_usd_exchange_rate()

    def __get_shape(self):
        """ Prints the shape of the dataset. Useful for quickly understanding the size of the dataset. """
        print("SHAPE OF THE APARTMENTS DATASET: ", self.apartments_df.shape)

    def __get_info(self):
        """ Prints detailed information about the dataset. Helpful for understanding the dataset structure. """
        print("THE APARTMENTS DATASET INFORMATION: ", self.apartments_df.info(), '\n')

    def __get_description(self):
        """ Prints a statistical summary of the dataset. Useful for a quick overview of data distribution. """
        print("DESCRIPTION OF THE APARTMENTS DATASET:\n", self.apartments_df.describe(), '\n')

    def __get_null_columns(self):
        """ Prints the count of missing (null) values for each column in the dataset. """
        print("AMOUNT OF NULL VALUES IN APARTMENTS DATASET: \n", self.apartments_df.isnull().sum(), '\n')

    def __clean_area_m2(self):
        """Clean area_m2 column by removing 'მ²' from strings and converting to numeric"""
        self.apartments_df['area_m2'] = self.apartments_df['area_m2'].apply(
            lambda x: x[:-2] if isinstance(x, str) and x.endswith('მ²') else x
        )
        self.apartments_df['area_m2'] = pd.to_numeric(self.apartments_df['area_m2'], errors='coerce')

    def __clean_and_transform_price(self):
        """ Removes the $ sign and converts to USD if in Georgian Lari or marks price as None if it's negotiable. """
        def parse_price(price):
            price_str = str(price).replace(',', '').strip().lower()

            try:
                if '$' in price_str:
                    return float(price_str.replace('$', '').strip())
                else:
                    return round(float(price_str) * self.currency_rate)
            except ValueError:
                return None
        self.apartments_df['price'] = self.apartments_df['price'].apply(parse_price)

    def __clean_price_per_sqm(self):
        def clean_row(row):
            if pd.isna(row['price_per_sqm']):
                try:
                    return int(row['price']) // int(row['area_m2'])
                except (TypeError, ZeroDivisionError):
                    return None

            value = str(row['price_per_sqm']).strip()
            if '/' in value:
                value = value.split('/')[0].strip()

            if '$' in value:
                value = value.replace('$', '').replace(',', '').strip()
                return float(value)
            else:
                value = value.replace(',', '').strip()
                return round(float(value) * self.currency_rate)

        self.apartments_df['price_per_sqm'] = self.apartments_df.apply(clean_row, axis=1)

    def __fill_district_name_nulls(self):
        """Fills missing values in the district_name column with a default message."""
        self.apartments_df['district_name'] = self.apartments_df['district_name'].fillna("არ არის მოწოდებული")
        print("NULL COLUMNS IN DISTRICT_NAME COLUMN HAVE BEEN FILLED")

    def __transform_upload_date(self):
        # Georgian abbreviated month names to numbers
        geo_months = {
            'იან': 1, 'თებ': 2, 'მარ': 3, 'აპრ': 4, 'მაი': 5, 'ივნ': 6,
            'ივლ': 7, 'აგვ': 8, 'სექ': 9, 'ოქტ': 10, 'ნოე': 11, 'დეკ': 12
        }

        # Ensure the column is string
        df = self.apartments_df.copy()
        df['upload_date'] = df['upload_date'].astype(str)

        def parse_date(upload_str):
            try:
                parts = upload_str.split()
                if len(parts) != 3:
                    return None
                day, geo_month_abbr, time_str = parts
                month = geo_months.get(geo_month_abbr[:3])
                if not month:
                    return None
                now = datetime.now()
                return datetime(year=now.year, month=month, day=int(day), hour=int(time_str[:2]),
                                minute=int(time_str[3:5]))
            except:
                return None

        # Apply to column
        df['upload_date'] = df['upload_date'].apply(parse_date)
        self.apartments_df = df

    def __new_transaction_type_col(self):
        """Extracts the transaction type from description and creates a new column."""

        def extract_transaction_type(desc):
            if not isinstance(desc, str):
                return None
            desc = desc.strip()
            if "იყიდება" in desc:
                return "იყიდება"
            elif "გირავდება" in desc:
                return "გირავდება"
            elif "ქირავდება დღიურად" in desc:
                return "ქირავდება დღიურად"
            elif "ქირავდება" in desc:
                return "ქირავდება თვიურად"
            else:
                return None

        self.apartments_df['transaction_type'] = self.apartments_df['description'].apply(extract_transaction_type)
        print("New column 'transaction_type' has been created based on descriptions.")

    def write_to_csv(self, path="data_output/cleaned_apartments.csv"):
        """ Writes the dataset to a csv file. """
        self.apartments_df.to_csv(path, index=False)

    def main(self):
        self.__get_shape()
        self.__get_info()
        self.__get_description()
        self.__get_null_columns()

        self.__clean_and_transform_price()
        self.__clean_area_m2()
        self.__clean_price_per_sqm()

        self.__transform_upload_date()
        self.__new_transaction_type_col()

        self.__fill_district_name_nulls()
        self.__get_null_columns()
