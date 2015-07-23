
import sirius


def get_record_names(family_name = None):

    if family_name == None:
        families = ['tsfk']
        record_names_dict = {}
        for i in range(len(families)):
            record_names_dict.update(get_record_names(families[i]))
        return record_names_dict

    if family_name.lower() == 'tsfk':
        _dict = {
                # 'TSFK-RESET':{},
                # 'TSFK-INJECT':{},
                # 'TSFK-DUMP':{},
        }

        get_element_names = sirius.ts.record_names.get_element_names

        # adds fake Corrector pvs for errors
        _dict.update(get_element_names('corr', prefix = 'TSFK-ERRORX-'))
        _dict.update(get_element_names('corr', prefix = 'TSFK-ERRORY-'))
        _dict.update(get_element_names('corr', prefix = 'TSFK-ERRORR-'))
        # adds fake BEND pvs for errors
        _dict.update(get_element_names('bend', prefix = 'TSFK-ERRORX-'))
        _dict.update(get_element_names('bend', prefix = 'TSFK-ERRORY-'))
        _dict.update(get_element_names('bend', prefix = 'TSFK-ERRORR-'))
        # adds fake SEP pvs for errors
        _dict.update(get_element_names('septa', prefix = 'TSFK-ERRORX-'))
        _dict.update(get_element_names('septa', prefix = 'TSFK-ERRORY-'))
        _dict.update(get_element_names('septa', prefix = 'TSFK-ERRORR-'))
        #adds fake QUAD pvs for errors
        _dict.update(get_element_names('quad', prefix = 'TSFK-ERRORX-'))
        _dict.update(get_element_names('quad', prefix = 'TSFK-ERRORY-'))
        _dict.update(get_element_names('quad', prefix = 'TSFK-ERRORR-'))

        return _dict

    else:
        raise Exception('Family name %s not found'%family_name)
