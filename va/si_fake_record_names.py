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

        # adds fake CF pvs for errors
        cfrn = sirius.si.record_names.get_record_names('chf')
        for key in cfrn.keys():
            value = cfrn[key]['chf']
            _dict[str.replace(key, 'SIPS-CHF', 'SIFK-ERRORX-CF')] = {'cf':value}
            _dict[str.replace(key, 'SIPS-CHF', 'SIFK-ERRORY-CF')] = {'cf':value}
            _dict[str.replace(key, 'SIPS-CHF', 'SIFK-ERRORR-CF')] = {'cf':value}
        # adds fake QUAD pvs for errors
        for quad_name in ('qfa', 'qda', 'qfb', 'qdb1', 'qdb2','qf1', 'qf2', 'qf3', 'qf4'):
            cfrn = sirius.si.record_names.get_record_names(quad_name)
            for key in cfrn.keys():
                value = cfrn[key][quad_name]
                _dict[str.replace(key, 'SIPS-', 'SIFK-ERRORX-')] = {quad_name:value}
                _dict[str.replace(key, 'SIPS-', 'SIFK-ERRORY-')] = {quad_name:value}
                _dict[str.replace(key, 'SIPS-', 'SIFK-ERRORR-')] = {quad_name:value}
        return _dict

    else:
        raise Exception('Family name %s not found'%family_name)
