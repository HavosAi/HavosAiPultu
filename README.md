# HavosAi

There are two main scripts in repo. One is used for converting .pdf files to .pkl files (text files) and called PDF_converted.ipynb and the second one is PSE_pipeline notebook (PSE_pipeline.ipynb).

!Important, for each of this notebooks there are different python enviroment, each folder contains the following files with should be run as commands in command line:
* env-create.cmd
* env-update.cmd
After successful running we can run the following run to start Jupyter Notebook:
*notebook.cmd 

Our entrypoints are Jupyter notebooks and should be run in Jupyter Hub.

To run pipeline we need correctly set up all variables (folders and files paths) in 2nd section called "Constant/variables". This section contains data for training (already reviewed articles) and test data (for which we should generate labels), apart from it section contains paths to all additional/useful files, e.g. mappings. All files are placed in data folder in github repo. For running the scripts, please download full repo and in 2ns section "Constant/variables" change DATA_FOLDER parameter.

Details about pipeline steps:
* Title extraction:
* Year extraction: for year extraction we are searching for first mentioned year in first 3 pages with condition that year should be placed between 1980 and 2022.
* Publishing Institution: institutions are extracted based on list provided in Airtable just using search.
* Countries: countries are extracted by names (using pycountry library), for each country we calculate frequency of mentioning, then based on frequency we select only countries with percentage of mentioning equal or greater than 1 / NUMBER_OF_ALL_MENTIONED_COUNTIERS, it helps to filter all "once mentioned countries".
* USAID-region: based on extracted and selected countries and USAID-region - country mapping file, we assign for each country region and then aggregate all regions.
* USAID-funded:
* Special consideration: because category has multioutput (one or more labels per sample), we train model for each labels separately, it means that number of models equals to number of different labels for Special consideration. Training set is split to train and test as 85% / 15%. After we apply obtained model to test set.
* PSE Ways We Engage: for generating labels, we are using student spans for training set; for test set we analyze 5 first pages sentence by sentence and trying to match sentence from text with each student span; therefore in the end we will have for text and all categories confidence score, which equals to maximum similarity between each pair of sentence text and all student spans for this category.
* PSE Key Values/ PSE Key Values USAID offer: the same approach as doe PSE Ways We Engage.


