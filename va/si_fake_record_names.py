
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

        get_element_names = sirius.si.record_names.get_element_names

        # adds fake CF pvs for errors
        cf_rn = get_element_names('chf', prefix = 'SIFK-ERRORX-')
        cf_rn.update(get_element_names('chf', prefix = 'SIFK-ERRORY-'))
        cf_rn.update(get_element_names('chf', prefix = 'SIFK-ERRORR-'))
        for key in cf_rn.keys():
            value = cf_rn[key]['chf']
            _dict[str.replace(key, '-CHF-', '-CF-')] = {'cf':value}
        # adds fake BEND pvs for errors
        _dict.update(get_element_names('bend', prefix = 'SIFK-ERRORX-'))
        _dict.update(get_element_names('bend', prefix = 'SIFK-ERRORY-'))
        _dict.update(get_element_names('bend', prefix = 'SIFK-ERRORR-'))
        #adds fake QUAD pvs for errors
        _dict.update(get_element_names('quad', prefix = 'SIFK-ERRORX-'))
        _dict.update(get_element_names('quad', prefix = 'SIFK-ERRORY-'))
        _dict.update(get_element_names('quad', prefix = 'SIFK-ERRORR-'))
        # adds fake SEXT pvs for errors
        _dict.update(get_element_names('sext', prefix = 'SIFK-ERRORX-'))
        _dict.update(get_element_names('sext', prefix = 'SIFK-ERRORY-'))
        _dict.update(get_element_names('sext', prefix = 'SIFK-ERRORR-'))

        return _dict        

    else:
        raise Exception('Family name %s not found'%family_name)
