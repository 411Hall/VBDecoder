#!/usr/bin/env python
import re
from collections import Counter
from optparse import OptionParser
import sys
import requests
import json
import datetime

decoded_vb = []

def main(input_file):
    try:
        vbscript_file = open(input_file, 'r')
        vbscript = vbscript_file.read()
        vbscript_file.close()
    except:
        print "\nFailed to open file, ensure path is correct.\n"
        sys.exit()

    ## Output Header
    decoded_vb.append("Imports System\nimports Microsoft.VisualBasic\nPublic Module Decoder\n")

    ## Extract Most Common Function Name
    regex_items = []
    func_name_regex = "[^a-zA-Z0-9]{1,}(.*?)\(\""
    for item in re.findall(func_name_regex, vbscript):
        regex_items = regex_items + re.split(r" |(?<![0-9])[.,](?![0-9])", item)
    func_count = Counter(regex_items)
    func_name = str(func_count.most_common(1)).split("'")[1]

    ## Get AND NOT, ASC and CHR Functions
    function_re = "Function(.*?)End Function"
    for function in re.findall(function_re, str(vbscript), flags=re.IGNORECASE|re.DOTALL):
        strings = ['and not', '=asc', '=chr']
        for string in strings:
            if string in function.lower():
                for line in function.split('\n'):
                    if re.match("^[a-zA-Z0-9]{1,30}=[0-9]{1,5}", line):
                        function = function.replace(line, '')
                decoded_vb.append("Function{0}End Function\n".format(function))

    ## Get Main Function
    main_re = "Function {0}(.*?)End Function".format(func_name)
    for main in re.findall(main_re, vbscript, flags=re.IGNORECASE|re.DOTALL):
        for line in main.split('\n'):
            if re.match("^[a-zA-Z0-9]{1,30}=[0-9]{1,5}", line):
                main = main.replace(line, '')
        decoded_vb.append("Function {0}{1}End Function\n".format(func_name,main))

    ## Get Decryption Routine Value\Key
    decryption_re = "\(\"(.*?)\)"
    decoded_vb.append("Public Sub Main()")
    for value in re.findall(decryption_re, vbscript):
        if "\"" not in value.split(',')[1]:
            variable_re = "{0}=(\".*)".format(value.split(',')[1])
            for var in re.findall(variable_re,vbscript):
                key = value.split(',')[0]
                decoded_vb.append("Console.WriteLine({0}(\"{1},{2}))".format(func_name,key, var.strip()))
        else:
            pass
            decoded_vb.append("Console.WriteLine({0}(\"{1}))".format(func_name, value))

    ## Output Footer
    decoded_vb.append("End Sub\nEnd Module")

def netfiddle(codeblock):
    code = ""
    ## Break VBScript code array line by line
    for line in codeblock:
        code = code + line + "\n"

    ## Submit data to .NET Fiddle
    api_link = "https://dotnetfiddle.net/api/fiddles/execute/"
    data = {"Language": "VBNET", "ProjectType": "Console", "Compiler": "Net45", "CodeBlock": code}

    ## Read API Limit, JSON Reponses
    response = requests.post(api_link, data=data)
    response_json = response.json()
    apirequests = response.headers["x-ratelimit-remaining"]
    apirequestreset = response.headers["x-ratelimit-reset"]
    ratelimitreset = int(apirequestreset)

    ## Output to Screen
    print "\nAPI Requests Remaining: {0}".format(apirequests)
    print "API Limit Resets at: {0}\n".format(datetime.datetime.fromtimestamp(ratelimitreset).strftime('%Y-%m-%d %H:%M'))
    print ".NET Fiddle Console Output\n--------------------"
    print response_json["ConsoleOutput"]
    print "--------------------\n"

def outputtofile(decoded_vb, filename):
    outfile = open(filename, 'w')
    for line in decoded_vb:
        outfile.write(line + "\n")
    outfile.close()

def outputtoscreen(decoded_vb):
    print "-------------"
    for line in decoded_vb:
        print line
    print "-------------\n\nNow copy to https://dotnetfiddle.net and create a VB.NET Console project.\n"


if __name__ == "__main__":
    parser = OptionParser(usage='usage: %prog VBScript [options]')
    parser.add_option("-o", "--output", action='store_true', default='False', help="Output decoded VBS to a text file (/path/to/file)")
    parser.add_option("-d", "--dotnet", action='store_true', default='False', help="Submit parsed VBS to .NET Fiddle & Output to Screen")
    (options, args) = parser.parse_args()
    if len(args) < 1:
        print "[!] Not enough Arguments, Need at least file path"
        parser.print_help()
        sys.exit()

    if options.dotnet is True:
        main(args[0])
        netfiddle(decoded_vb)
        sys.exit()

    elif options.output is True:
        main(args[0])
        outputtofile(decoded_vb, args[1])
        sys.exit()

    else:
        main(args[0])
        outputtoscreen(decoded_vb)


