import sirius


def get_record_names(family_name = None):

    if family_name == None:
        families = ['sifk',]
        record_names_dict = dict()
        for i in range(len(families)):
            record_names_dict.update(get_record_names(families[i]))
        return record_names_dict

    if family_name.lower() == 'sifk':
        _dict = {
                'SIFK-RESET':{},
                'SIFK-INJECT':{},
                'SIFK-DUMP':{},
        }

        # adds fake fake CHS and CVS pvs for errors
        cfrn = sirius.si.record_names.get_record_names('chf')
        for key in cfrn.keys():
            value = cfrn[key]['chf']
            _dict[str.replace(key, 'SIPS-CHF', 'SIFK-CF-ERRORX')] = {'cf':value}
            _dict[str.replace(key, 'SIPS-CHF', 'SIFK-CF-ERRORY')] = {'cf':value}
            _dict[str.replace(key, 'SIPS-CHF', 'SIFK-CF-ERRORR')] = {'cf':value}
        return _dict

    else:
        raise Exception('Family name %s not found'%family_name)
