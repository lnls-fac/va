
def get_record_names(family_name = None):

    if family_name == None:
        families = ['tsfk']
        record_names_dict = {}
        for i in range(len(families)):
            record_names_dict.update(get_record_names(families[i]))
        return record_names_dict

    if family_name.lower() == 'tsfk':
        _dict = {
                'TSFK-RESET':{},
                'TSFK-INJECT':{},
                'TSFK-DUMP':{},
        }
        return _dict

    else:
        raise Exception('Family name %s not found'%family_name)
