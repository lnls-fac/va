
import sirius


def get_record_names(family_name = None):

    if family_name == None:
        families = ['tbfk']
        record_names_dict = {}
        for i in range(len(families)):
            record_names_dict.update(get_record_names(families[i]))
        return record_names_dict

    if family_name.lower() == 'tbfk':
        _dict = {
                'TBFK-RESET':{},
                'TBFK-INJECT':{},
                'TBFK-DUMP':{},
        }

        get_element_names = sirius.tb.record_names.get_element_names

        # adds fake Corrector pvs for errors
        _dict.update(get_element_names('corr', prefix = 'TBFK-ERRORX-'))
        _dict.update(get_element_names('corr', prefix = 'TBFK-ERRORY-'))
        _dict.update(get_element_names('corr', prefix = 'TBFK-ERRORR-'))
        # adds fake BEND pvs for errors
        _dict.update(get_element_names('bend', prefix = 'TBFK-ERRORX-'))
        _dict.update(get_element_names('bend', prefix = 'TBFK-ERRORY-'))
        _dict.update(get_element_names('bend', prefix = 'TBFK-ERRORR-'))
        # adds fake SEP pvs for errors
        _dict.update(get_element_names('sep', prefix = 'TBFK-ERRORX-'))
        _dict.update(get_element_names('sep', prefix = 'TBFK-ERRORY-'))
        _dict.update(get_element_names('sep', prefix = 'TBFK-ERRORR-'))
        #adds fake QUAD pvs for errors
        _dict.update(get_element_names('quad', prefix = 'TBFK-ERRORX-'))
        _dict.update(get_element_names('quad', prefix = 'TBFK-ERRORY-'))
        _dict.update(get_element_names('quad', prefix = 'TBFK-ERRORR-'))

        return _dict

    else:
        raise Exception('Family name %s not found'%family_name)
