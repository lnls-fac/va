
import sirius


def get_record_names(family_name = None):

    if family_name == None:
        families = ['bofk']
        record_names_dict = {}
        for i in range(len(families)):
            record_names_dict.update(get_record_names(families[i]))
        return record_names_dict

    if family_name.lower() == 'bofk':
        _dict = {
                'BOFK-RESET':{},
                'BOFK-INJECT':{},
                'BOFK-DUMP':{},
        }

        get_element_names = sirius.bo.record_names.get_element_names

        # adds fake Corrector pvs for errors
        _dict.update(get_element_names('corr', prefix = 'BOFK-ERRORX-'))
        _dict.update(get_element_names('corr', prefix = 'BOFK-ERRORY-'))
        _dict.update(get_element_names('corr', prefix = 'BOFK-ERRORR-'))
        # adds fake BEND pvs for errors
        _dict.update(get_element_names('bend', prefix = 'BOFK-ERRORX-'))
        _dict.update(get_element_names('bend', prefix = 'BOFK-ERRORY-'))
        _dict.update(get_element_names('bend', prefix = 'BOFK-ERRORR-'))
        #adds fake QUAD pvs for errors
        _dict.update(get_element_names('quad', prefix = 'BOFK-ERRORX-'))
        _dict.update(get_element_names('quad', prefix = 'BOFK-ERRORY-'))
        _dict.update(get_element_names('quad', prefix = 'BOFK-ERRORR-'))
        # adds fake SEXT pvs for errors
        _dict.update(get_element_names('sext', prefix = 'BOFK-ERRORX-'))
        _dict.update(get_element_names('sext', prefix = 'BOFK-ERRORY-'))
        _dict.update(get_element_names('sext', prefix = 'BOFK-ERRORR-'))

        return _dict

    else:
        raise Exception('Family name %s not found'%family_name)
