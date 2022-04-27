import sys

# importing required modules 
from dataclasses import replace
import PyPDF2 
    
# creating a pdf file object 
pdfFileObj = open('./f/'+str(sys.argv[1])+'.pdf', 'rb') 
    
# creating a pdf reader object 
pdfReader = PyPDF2.PdfFileReader(pdfFileObj) 
    
# printing number of pages in pdf file 
# print(pdfReader.numPages) 
    
for n in range(0, pdfReader.numPages):
  # creating a page object 
  pageObj = pdfReader.getPage(n) 
      
  # extracting text from page 
  print(pageObj.extractText().replace('\n',' ').replace('  ', ' ')) 
    
# closing the pdf file object 
pdfFileObj.close() 