import sirius

def get_record_names(family_name = None):

    family_data = sirius.bo._lattice._family_data

    if family_name == None:
        families = ['bofk']
        record_names_dict = {}
        for i in range(len(families)):
            record_names_dict.update(get_record_names(families[i]))
        return record_names_dict

    if family_name.lower() == 'bofk':
        _dict = {
                'BOFK-INJECT':{},
                'BOFK-DUMP':{},
        }
        return _dict

    else:
        raise Exception('Family name %s not found'%family_name)