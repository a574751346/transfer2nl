import os
from bs4 import BeautifulSoup as BS
import json
import nltk.tokenize as tk
from bs4.element import NavigableString 

def extractWCS(ext="valid"):
    datas = []
    pk = tk.WordPunctTokenizer()
    with open("{}.json".format(ext), "r", encoding="utf8") as f:
        for line in f.readlines():
            line = json.loads(line)
            line["code"] = line["code"].replace("\n", " ")
            tkwords = " ".join(tk.word_tokenize(line["code"]))
            pkwrods = " ".join(pk.tokenize(tkwords))
            okwords = pkwrods.replace("! =", "!=").replace("= =", "==").replace("``", '"').replace("''", '"').replace("+ +", "++").replace("- -", "--").replace("< <", "<<").replace("> >", ">>").replace("> =", ">=").replace("< =", "<=").replace("& &", "&&").replace("| |", "||")
            line['code'] = okwords
            datas.append(line)
            # print(json.loads(line))

    
    # fileList = os.listdir("./xmls/")
    # print(fileList[:10])
    data_l = len(datas)
    dict_ = {}
    with open("./{}.token.wcs".format(ext), "w+", encoding="utf-8") as f:
        index = 0
        error_list = []
        for data in datas:
            index += 1
            if index % 100 == 0:
                print("[extract wcs]now the step is {}/{}".format(index, data_l))
            try:
                ### code 2 srcml 
                with open("./tmp.java", "w", encoding="utf-8") as tf:
                    tf.write(data['code'])
                # cmd = 'srcml -l Java --text "{}"'.format(data["code"])
                cmd = 'srcml tmp.java'
                # print(cmd)
                pp = os.popen(cmd)
                xmls = pp.read()

                id_ = data["id"]
                # dict_[id_] = set()
                dict_[id_] = set()
                # xmls = BS(open("./xmls/{}".format(file_)), "xml")
                xmls = BS(xmls, "xml")

                ### replace literal
                literals = xmls.find_all("literal")
                for literal in literals:
                    if literal['type'] == "number":
                        literal.string = "_NUM"
                    elif literal['type'] == "char":
                        literal.string = "_CHAR"
                    elif literal['type'] == "string":
                        literal.string = "_STR"
                    elif literal['type'] == "boolean":
                        literal.string = "_BOOL"
                    elif literal['type'] == "null":
                        literal.string = "_NULL"



                # print(len(xmls.function.children))
                flag = 1
                f.write(str(id_)+"\t")
                # print(xmls.prettify())
                # print(xmls.text)
                if xmls.function:
                    for _name in xmls.function.children:
                        if _name.name == "type":
                            flag = 0
                            f.write(_name.text+" ")
                        if _name.name == "name":
                            flag = 0
                            f.write(_name.text+" ")
                        if _name.name == "parameter_list":
                            flag = 0
                            f.write(_name.text)
                            break
                elif xmls.constructor:
                    for _name in xmls.constructor.children:
                        if _name.name == "name":
                            flag = 0
                            f.write(_name.text+" ")
                        if _name.name == "parameter_list":
                            flag = 0
                            f.write(_name.text)
                            break
                else:
                    flag = 0
                    f.write(xmls.find("name").text+" ")
                    
                if flag:
                    print(xmls.prettify())
                    print(xmls.text)
                    print("\nerror function name!\n")
                    break


                #-----------------------------------
                # voidReturn stmt extraction
                #-----------------------------------
                expr_stmt = xmls.find_all("expr_stmt")
                no_return = []
                for s in expr_stmt:
                    # print(s)
                    eq = s.find("operator", string="=")
                    # print(eq)
                    if eq is None:
                        no_return.append(s)
                    else:
                        continue 
                [dict_[id_].add(r) for r in no_return]

                #-----------------------------------
                # exitNode stmt extraction
                #-----------------------------------
                
                returns = xmls.find_all("return")
                all_expr = xmls.find_all("expr_stmt")
                if len(all_expr) > 0 :
                    dict_[id_].add(all_expr[-1])
                [dict_[id_].add(r) for r in returns]


                #-----------------------------------
                # sameaction stmt extraction
                #-----------------------------------
                
                #-----------------------------------
                # control flow stmt extraction
                #-----------------------------------
                
                for s in dict_[id_]:
                    control_flow_str = ""
                    # print(s.parents)
                    for p in s.parents:
                        ### If branch
                        if p.name == "if":
                            if control_flow_str != "":
                                control_flow_str = " " + control_flow_str
                            control_flow_str = "if " + p.condition.text + control_flow_str
                            if p.type == "elseif":
                                t = p
                                for ps in t.previous_siblings:
                                    control_flow_str = "ifnot " + ps.condition.text + " and " + control_flow_str
                        if p.name == "else":
                            if control_flow_str != "":
                                control_flow_str = " and " + control_flow_str
                            t = p
                            for ps in t.previous_siblings:
                                if isinstance(ps, NavigableString):
                                    continue
                                control_flow_str = "ifnot " + ps.condition.text + control_flow_str
                      

                        ### For branch 
                        if p.name == "for":
                            if control_flow_str != "":
                                control_flow_str = " and " + control_flow_str
                            control_flow_str = "for " + p.control.text + control_flow_str
                            
                        ### While branch 
                        if p.name == "while":
                            if control_flow_str != "":
                                control_flow_str = " and " + control_flow_str
                            control_flow_str = "while " + p.condition.text + control_flow_str

                    if len(control_flow_str) > 0:
                        f.write(" {} then {}".format(control_flow_str, s.text))
                    else:
                        f.write(" {}".format(s.text))
                    # print("<---end---->")
                f.write("\n")
            except IOError:
                error_list.append(index)
                return
        



def addTags(filetype="valid", datatype='tags'):
    filename = "./{}.token.code".format(filetype)
    trgname = './{}.token.{}'.format(filetype, datatype)

    datas = []
    print("start loading token.code...")
    index = 0
    with open(filename, "r") as f:
        for fileline in f.readlines():
            line = dict(zip(['id', 'code'], fileline.split('\t')))
            datas.append(line)
            index += 1 
            if index % 1000 == 0:
                print("[loading]now the step is {}/{}".format(index, len(datas)))

    index = 0
    print("token start adding tags...")
    dict_ = {}
    with open(trgname, "w+", encoding="utf-8") as f:
        error_list = []
        for data in datas:
            try:
                ### code 2 srcml 
                with open("./tmp.java", "w", encoding="utf-8") as tf:
                    tf.write(data['code'])
                cmd = 'srcml tmp.java'
                pp = os.popen(cmd)
                xmls = pp.read()

                id_ = data["id"]
                dict_[id_] = set()
                xmls = BS(xmls, "xml")
                for d in xmls.descendants:
                    # 21
                    if d.name in ["parameter","type","literal","block","do","for","condition","if","return","switch","case","while","control","then","lambda","call","ternary","init","try","operator"]:
                        if d.string:
                            d.string = d.name + "_b " + d.string + " " + d.name + "_e"
                        else:
                            d.insert(0, d.name + "_b ")
                            d.insert(len(d.contents), " " + d.name + "_e")
                            
                index += 1
                if index % 100 == 0:
                    print("[adding tags]now the step is {}/{}".format(index, len(datas)))
                f.write(str(id_)+"\t" + xmls.text)
            except IOError:
                error_list.append(id_)
                continue
                
        
        print(error_list)


def prepareCodeAndNl(filetype='valid'):
    filename = "./{}.json".format(filetype)
    trgname_code = './{}.token.code'.format(filetype)
    trgname_nl = './{}.token.nl'.format(filetype)
    datas = []
    # tokenizer = tk.word_tokenize()
    pk = tk.WordPunctTokenizer()
    index = 0
    print("token start parsing...")
    with open(filename, "r") as f:
        ff = f.readlines()
        for line in ff:
            line = json.loads(line)
            line["code"] = line["code"].replace("\n", " ")
            tkwords = " ".join(tk.word_tokenize(line["code"]))
            pkwrods = " ".join(pk.tokenize(tkwords))
            okwords = pkwrods.replace("! =", "!=").replace("= =", "==").replace("``", "''").replace('"', "'").replace("+ +", "++").replace("- -", "--").replace("< <", "<<").replace("> >", ">>").replace("> =", ">=").replace("< =", "<=").replace("& &", "&&").replace("| |", "||")
            # print(okwords)
            line['code'] = okwords
            line['nl'] = " ".join(tk.word_tokenize(line['nl']))
            datas.append(line)
            index += 1 
            if index % 1000 == 0:
                print("[token code&nl]now the step is {}/{}".format(index, len(ff)))

    print("token start writing...")
    with open(trgname_code, "w+", encoding='utf8') as fc, open(trgname_nl, "w+", encoding='utf8') as fn:
        for line in datas:
            fc.write("{}\t{}\n".format(line['id'], line['code']))
            fn.write("{}\t{}\n".format(line['id'], line['nl']))

# prepareCodeAndNl("test")
# extractWCS("test")

def prepareVocab(datatype='wcs'):
    trgname = './vocab.{}'.format(datatype)
    dict_ = {}
    index = 0
    print("[vocab]start parsing...")
    with open("./train/train.token.{}".format(datatype), "r") as f:
        ff = f.readlines()
        for line in ff:
            words = line.split('\t')[1].split()
            for word in words:
                if word in dict_:
                    dict_[word] += 1
                else:
                    dict_[word] = 1
            index += 1 
            if index % 1000 == 0:
                print("[vocab]now the step is {}/{}".format(index, len(ff)))
    index = 0
    with open("./test/test.token.{}".format(datatype), "r") as f:
        ff = f.readlines()
        for line in ff:
            words = line.split('\t')[1].split()
            for word in words:
                if word in dict_:
                    dict_[word] += 1
                else:
                    dict_[word] = 1
            index += 1 
            if index % 1000 == 0:
                print("[vocab]now the step is {}/{}".format(index, len(ff)))
    index = 0
    with open("./valid/valid.token.{}".format(datatype), "r") as f:
        ff = f.readlines()
        for line in ff:
            words = line.split('\t')[1].split()
            for word in words:
                if word in dict_:
                    dict_[word] += 1
                else:
                    dict_[word] = 1
            index += 1 
            if index % 1000 == 0:
                print("[vocab]now the step is {}/{}".format(index, len(ff)))

    dict_ = sorted(dict_.items(), key=lambda d:d[1], reverse = True)

    print("vocab start writing...")
    with open(trgname, "w+", encoding='utf8') as f:
        for s in ['<S>', '<UNK>', '<KEEP>', '<DEL>', '<INS>', '<SUB>', '<NONE>']:
            f.write("{}\n".format(s))

        for k in dict_[:49993]:
            f.write("{}\n".format(k[0]))


# prepareCode("test", "code")
# addTags("test", "tags")

prepareVocab("nl")
prepareVocab("code")

def preprocess():
    with open("./valid.token.code") as f:
        line = tuple(f.readline().split("\t"))
        cmd = "srcml --xpath '//src:function/src:name' -l Java --text '{}'".format(line[1])
        # print(cmd)
        res = os.system(cmd)
        print("--------------")
        print(res)

def returenStat():
    fileList = os.listdir("./xmls/")
    # print(fileList[:10])
    for file_ in fileList[:10]:
        xmls = BS(open("./xmls/{}".format(file_)), "xml")
        # print(xmls.prettify())
        returns = xmls.find_all("return")
        returns = [r.text for r in returns]
            # print(returns)
        print(" ".join(returns))
        # print(len(returns))

def voidReturn():
    fileList = os.listdir("./xmls/")
    # print(fileList[:10])
    dict_ = {}
    with open("./stmts", "w+") as f:
        for filename in fileList[:10]:
            print("index: ", filename)
            id_ = filename.split(".")[0]
            dict_[id_] = set()
            # xmls = BS(open("./xmls/{}".format(file_)), "xml")
            xmls = BS(open("./xmls/{}.xml".format(id_)), "xml")

            # print(xmls.function)
            # print(len(xmls.function.children))
            flag = 1
            f.write(id_+"\t")
            for _name in xmls.function.children:
                print(_name)
                if _name.name == "name":
                    flag = 0
                    f.write(_name.text)
                    break
                
            if flag:
                print("\nerror function name!\n")
                break

            #-----------------------------------
            # voidReturn stmt extraction
            #-----------------------------------
            expr_stmt = xmls.find_all("expr_stmt")
            no_return = []
            for s in expr_stmt:
                # print(s)
                eq = s.find("operator", string="=")
                # print(eq)
                if eq is None:
                    no_return.append(s)
                else:
                    continue 
            [dict_[id_].add(r) for r in no_return]


            # f.write(file_.split(".")[0]+"\t"+(" ".join(no_return)+"\n"))
            # print(" ".join(no_return))
            # print([r.text for r in xmls.find_all("call")])


            #-----------------------------------
            # exitNode stmt extraction
            #-----------------------------------
            
            returns = xmls.find_all("return")
            all_expr = xmls.find_all("expr_stmt")
            if len(all_expr) > 0 :
                dict_[id_].add(all_expr[-1])
            [dict_[id_].add(r) for r in returns]


            #-----------------------------------
            # sameaction stmt extraction
            #-----------------------------------
            


            #-----------------------------------
            # control flow stmt extraction
            #-----------------------------------
            # xml.find_all("if")
            # xml.find_all("for")
            # xml.find_all("while")
            # for k in dict_:
            #     print([s.text for s in dict_[k]])
            for s in dict_[id_]:
                flag = 0
                cond = s.find_parents("if")
                
                if len(cond) == 1:
                    f.write(" if "+cond[0].condition.text+" then "+s.text)
                elif len(cond) == 0:
                    flag += 1
                else:
                    print("error!!!!")
                # print(cond[0].condition.text)
                # print(cond[0].text)

                cond = s.find_parents("for")
                # print(cond)
                if len(cond) == 1:
                    # print(cond[0])
                    f.write(" for "+cond[0].control.text+" then "+s.text)
                elif len(cond) == 0:
                    flag += 1
                else:
                    print("error!!!!")

                cond = s.find_parents("while")
                # print(cond)
                if len(cond) == 1:
                    f.write(" while "+cond[0].condition.text+" then "+s.text)
                elif len(cond) == 0:
                    flag += 1
                else:
                    print("error!!!!")

                cond = s.find_parents("switch")
                # print(cond)
                if len(cond) == 1:
                    f.write(" if "+cond[0].condition.text+" then "+s.text)
                elif len(cond) == 0:
                    flag += 1
                else:
                    print("error!!!!")
        
                if (flag == 4):
                    f.write(" "+s.text)
            f.write("\n")




# voidReturn()
# returenStat()

def extract():
    with open("valid.token.code") as f:
        line = tuple(f.readline().split("\t"))

        print("id: {} \ncontent: {}".format(line[0],line[1]))

        res = set()

        ### code 2 srcml 
        # print(line[1])
        cmd = 'srcml -l Java --text "{}"'.format(line[1])
        pp = os.popen(cmd)
        xmls = pp.read()

        ### return statement
        xmls = BS(xmls, "xml")
        # print(xmls.prettify())
        returns = xmls.find_all("return")
        [res.add(r) for r in returns]
        # print(returns)

        ### void return statement
        print(" ".join(res))



def Extract():
    datas = []
    tokenizer = tk.WordPunctTokenizer()
    with open("valid.json", "r") as f:
        for line in f.readlines():
            line = json.loads(line)
            line["code"] = line["code"].replace("\n", " ")
            #print(tokenizer.tokenize(line["code"]))
            # print(tk.word_tokenize(line["code"]))
            line["code"] = " ".join(tokenizer.tokenize(line["code"]))
            datas.append(line)

            # print(json.loads(line))

    
    # fileList = os.listdir("./xmls/")
    # print(fileList[:10])
    dict_ = {}
    with open("./train.token.api", "w+", encoding="utf-8") as f:
        index = 0
        error_list = []
        for data in datas:
            index += 1
            try:
                ### code 2 srcml 
                # print(line[1])
                # print(data["code"])
                with open("./tmp.java", "w", encoding="utf-8") as tf:
                    tf.write(data['code'])
                # cmd = 'srcml -l Java --text "{}"'.format(data["code"])
                cmd = 'srcml tmp.java'
                # print(cmd)
                pp = os.popen(cmd)
                xmls = pp.read()

                print("index: {}, id: {}".format(index,data["id"]))
                id_ = data["id"]
                # dict_[id_] = set()
                dict_[id_] = set()
                # xmls = BS(open("./xmls/{}".format(file_)), "xml")
                xmls = BS(xmls, "xml")

                # print(xmls.function)
                # print(len(xmls.function.children))
                flag = 1
                f.write(str(id_)+"\t")
                # print(xmls)
                # print(xmls.text)
                if xmls.function:
                    for _name in xmls.function.children:
                        # print(_name)
                        if _name.name == "name":
                            flag = 0
                            f.write(_name.text)
                            break
                elif xmls.constructor:
                    f.write(xmls.constructor.find("name").text)
                    flag = 0
                    
                if flag:
                    print("\nerror function name!\n")
                    f.write(xmls.find("name").text)

                #-----------------------------------
                # voidReturn stmt extraction
                #-----------------------------------
                expr_stmt = xmls.find_all("expr_stmt")
                no_return = []
                for s in expr_stmt:
                    # print(s)
                    eq = s.find("operator", string="=")
                    # print(eq)
                    if eq is None:
                        no_return.append(s)
                    else:
                        continue 
                [dict_[id_].add(r) for r in no_return]


                # f.write(file_.split(".")[0]+"\t"+(" ".join(no_return)+"\n"))
                # print(" ".join(no_return))
                # print([r.text for r in xmls.find_all("call")])


                #-----------------------------------
                # exitNode stmt extraction
                #-----------------------------------
                
                returns = xmls.find_all("return")
                all_expr = xmls.find_all("expr_stmt")
                if len(all_expr) > 0 :
                    dict_[id_].add(all_expr[-1])
                [dict_[id_].add(r) for r in returns]


                #-----------------------------------
                # sameaction stmt extraction
                #-----------------------------------
                


                #-----------------------------------
                # control flow stmt extraction
                #-----------------------------------
                # xml.find_all("if")
                # xml.find_all("for")
                # xml.find_all("while")
                # for k in dict_:
                #     print([s.text for s in dict_[k]])
                for s in dict_[id_]:
                    # print("<---start---->")
                    # print(s)
                    control_flow_str = ""
                    else_flow = 0
                    for p in s.parents:
                        # print(p.name)
                        ### If branch
                        if p.name == "if":
                            control_flow_str = "if " + p.condition.text + " "

                        ### TODO else branch process
                        '''
                        if p.name == "else":
                            else_flow = 1
                        if else_flow and p.name == "if_stmt":
                            control_flow_str = "if " + p.condition.text
                        '''

                        ### For branch 
                        if p.name == "for":
                            control_flow_str = "for " + p.control.text + " "
                            
                        ### While branch 
                        if p.name == "while":
                            control_flow_str = "while " + p.condition.text + " "

                    if len(control_flow_str) > 0:
                        f.write(" {} then {}".format(control_flow_str, s.text))
                    else:
                        f.write(" {}".format(s.text))
                    # print("<---end---->")
                f.write("\n")
            except IOError:
                return
            else:
                error_list.append(index)
        
        print(error_list)

        
    return

    print("<--------start------->")
    print(s.text)
    flag = 0
    cond = s.find_parents("if")
    print(len(cond))
    print(cond)
    if len(cond) == 1:
        f.write(" if "+cond[0].condition.text+" then "+s.text)
    elif len(cond) == 0:
        flag += 1
    else:
        print("error!!!!")
    # print(cond[0].condition.text)
    # print(cond[0].text)

    cond = s.find_parents("for")
    # print(cond)
    if len(cond) == 1:
        # print(cond[0])
        f.write(" for "+cond[0].control.text+" then "+s.text)
    elif len(cond) == 0:
        flag += 1
    else:
        print("error!!!!")

    cond = s.find_parents("while")
    # print(cond)
    if len(cond) == 1:
        f.write(" while "+cond[0].condition.text+" then "+s.text)
    elif len(cond) == 0:
        flag += 1
    else:
        print("error!!!!")

    cond = s.find_parents("switch")
    # print(cond)
    if len(cond) == 1:
        f.write(" if "+cond[0].condition.text+" then "+s.text)
    elif len(cond) == 0:
        flag += 1
    else:
        print("error!!!!")

    if (flag == 4):
        f.write(" "+s.text)

        
    print("<--------end------->")



