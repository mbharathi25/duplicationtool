
"""
Identifiers="Case No:", "Neutral Citation Number:"
"""

"""
Workflow: 
1. Go to appropriate directory.
2. Iterate through the files in a directory.
3. Open a file
3.1. If the file is a .rtf file, convert it to .txt. 
If target system is macOS, it'll be easy to do using os.command(textutil -convert txt <filename>.rtf)
4. Read file (should contain Metadata).
5. Find index of "court case number" or any other identifier
6. Make a dictionary. Key(court_case_number)->Value(list of files it occurs in)
7. Update dictionary for each file in the directory.

8. Return dictionary. Print it out in a readable format

cases dict structure:
{
    "case no./NCN":{"count":int, "appears_in":["file1", "file3"]} 
}

dictionary of files to manually examine:

{
    "Manually_Examine":["file1","file2"]
}
"""

#importing the os module to navigate directories
import os 
#importing the regex module
import re
#importing textract to parse .docx and .pdf files.
import textract


main_path="./court_files" #NOTE for Windows machines the "/" should be replaced by "\"
identifiers=["Neutral Citation Number:","Case No:"]
text_files=[]

def choose_identifier():

    print("\nSelect an identifier from the list: ",identifiers)
    choice=-1
    #loop until choice is valid
    while (choice<=0 or choice>len(identifiers)):
        choice=int(input("\nPlease enter a number that corresponds to the identifier (in the list displayed above) you want to group the files by:\n Example: 1 for NCN, 2 for Case Number :"))

    return int(choice)


#maintains the dictionary of cases, which is the output
def update_cases_dict(cases_dict,identifier,case_file):

    if(identifier==-1):
        return 0
    
    if(".txt" in case_file):
            case_file=case_file.replace(".txt",".rtf")

    #update dictionary if case has already been encountered
    if identifier in cases_dict:

        #increasing the integer that tracks the number of files that the case appears in
        cases_dict[identifier]["count"]+=1

        new_list=cases_dict[identifier]["appears_in"]

        #adding the file name to the list that tracks the files that the case appears in
        new_list.append(case_file)
        cases_dict[identifier]["appears_in"]=new_list
                           
    #making a dictionary object and adding it to the dict, if the case has not been encountered yet.
    else:
        dict_entry={identifier:{"count":1,"appears_in":[case_file]}}
        cases_dict.update(dict_entry)

#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

#Takes a line, a list of files and the case file being looked at.Strips the "Case No:/ NCN: " prefix and returns only the identifier itself.
# If this isn't possible, it adds the case file to a list of files that have to be manually looked at and returns -1.
def get_only_identifier(parsed_line,troublesome_files,case_file,identifier):

    converted_line=re.sub(r"[\n\t]*", "", parsed_line)
    
    #print("Identifier is:",converted_line)
    converted_line=converted_line.replace(identifier,"")
    #print(f"{identifier} for {case_file}: ",converted_line)

    #EDGE CASE: if line is empty, meaning that the line only had an identifier and no value. Example: Case No: without the value
    if (len(converted_line.strip())<=1): 
        print(f"There seems to be an issue with getting the identifier for: {case_file} ")
        print("Adding this file to list of files that may have to be manually examined")
        troublesome_files.append(case_file)
        converted_line=-1

    return converted_line

#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

#Takes a line, checks if it has the identifier ("Case No:", for example) and returns a list [int,string] int is -1 if line doesn't have the identifier
def parse_line(line,file_type,identifier):
    case_num_index=line.find(identifier)
    return[case_num_index,line]
        
#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------

def convert_rtf_to_txt(): #converting .rtf files to .txt files for easier parsing

    files=os.listdir(main_path)

    for file in files:
        file_path=os.path.join(main_path,file)
        file_type=os.path.splitext(file_path)

        if(file_type[1]==".rtf"):
            os.system(f"textutil -convert txt '{file_path}' ") #only works on macOS
            text_file_path=file_path.replace(".rtf",".txt")
            #print("Text file path:", text_file_path)
            text_files.append(text_file_path)


def remove_txt_files():
    print("Removing these temporary text files, generated by the script",text_files)

    for file_path in text_files:
        try:
            os.remove(file_path)
        except OSError:
            print("Can't delete",file_path)


#------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------------
def driver():

    dir_contents=os.listdir(main_path)
    troublesome_files=[]
    identifier=identifiers[choose_identifier()-1]
    
    cases_dict={}
    print("Searching through files")

    #iterating through the files in each directory
    for case_file in dir_contents:
        file_path=os.path.join(main_path,case_file)
        file_type=os.path.splitext(file_path)

        #move to the next file if the file is not one of the specified types
        if(file_type[1]!=".pdf" and file_type[1]!=".docx" and file_type[1]!=".txt"):
            continue

        #if file is valid type, read it
        print("Reading file: ",case_file)
        try:
            #opening the file using python's open method
            opened_file= open(file=file_path,mode="r")
            #file_type is an array of 2 elements, the second of which will contain the file extension
            identifier_found=-1

            #parsing a pdf or docx file and converting it into a list of lines
            if(file_type[1]==".pdf" or file_type[1]==".docx"):
                content=textract.process(file_path)
                file_content=content.decode("utf-8")
                file_content=file_content.splitlines()
                
            #probably going to be .rtf files which would be converted to .txt files temporarily by the script
            else:
                file_content=opened_file.readlines()

            line_count=0
            #reading until end of file content or until identifier is found
            while(line_count<len(file_content)):
     
                line=str(file_content[line_count])
                parsed_line=parse_line(line,file_type[1],identifier)

                #if the identifier has been found
                if(parsed_line[0]!=-1): 
                    identifier_found=parsed_line[0]
                    #removing tabs, and new lines from the line if any. Retrieving only the Case number without the "Case No: prefix"
                    extracted_identifier=get_only_identifier(parsed_line[1],troublesome_files,case_file,identifier)
                    update_cases_dict(cases_dict,extracted_identifier,case_file)
                    break #stop reading the file
                    
                line_count+=1
                
            #if the identifier was not able to be found in the file at all (usually due to poor rtf parsing)
            if(identifier_found==-1):
                if(".txt" in case_file):
                    case_file=case_file.replace(".txt",".rtf")
                print(f"There seems to be an issue with getting the identifier for: {case_file} ")
                print("Adding this file to list of files that may have to be manually examined")
                troublesome_files.append(case_file)
                
            #closing the file 
            opened_file.close()

        except(FileNotFoundError):
                print(f"File at path: {file_path} does not exist")

    return{identifier:cases_dict,"Manually_Examine":troublesome_files}



#the workflow below

#converting rtf files to txt files
convert_rtf_to_txt()

#getting the output of the script
returned_dict=driver()
#print("dict",returned_dict)

#printing out the dictionary of files
dict_identifiers=list(returned_dict.keys())

print("-------------------------------------OUTPUT-------------------------------------------------------------")
for identifier in returned_dict[dict_identifiers[0]]:
    #print("Identifier",identifier)
    files=returned_dict[dict_identifiers[0]][identifier]["appears_in"]
    #print(files)
    print(f"\nThe {dict_identifiers[0]}: {identifier} can be found in these files: {files}")

print("\n\nManually Examine these files",returned_dict["Manually_Examine"])
print("-------------------------------------END_OF_OUTPUT-------------------------------------------------------------")

remove_txt_files()
