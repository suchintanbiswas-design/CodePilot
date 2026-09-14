def process_everything(data_payload, user_context, system_flags, env_vars, overrides):
    # Critical maintainability nightmare
    # Massive function, deeply nested, many if/elif, no error handling, magic numbers
    
    result = {}
    
    if data_payload != None:
        if type(data_payload) == list:
            if len(data_payload) > 0:
                for item in data_payload:
                    if item.get('type') == 1:
                        if item.get('val') > 100:
                            if user_context.get('role') == 'admin':
                                if system_flags.get('debug') == 1:
                                    print("Processing high value admin item")
                                    result['hv_admin'] = item.get('val') * 1.5
                                elif system_flags.get('debug') == 2:
                                    result['hv_admin'] = item.get('val') * 2.0
                                else:
                                    result['hv_admin'] = item.get('val') * 1.1
                            elif user_context.get('role') == 'manager':
                                if system_flags.get('strict') == 1:
                                    result['hv_mgr'] = item.get('val') * 0.9
                                else:
                                    result['hv_mgr'] = item.get('val')
                            else:
                                result['hv_usr'] = item.get('val') * 0.5
                        elif item.get('val') > 50:
                            if user_context.get('role') == 'admin':
                                result['mv_admin'] = item.get('val') * 1.2
                            else:
                                result['mv_usr'] = item.get('val') * 0.8
                        else:
                            result['lv'] = item.get('val')
                    elif item.get('type') == 2:
                        if env_vars.get('MODE') == 'prod':
                            if overrides.get('skip_type_2') != True:
                                for sub_item in item.get('children', []):
                                    if sub_item.get('status') == 5:
                                        if 't2_prod' not in result:
                                            result['t2_prod'] = []
                                        result['t2_prod'].append(sub_item.get('id'))
                        elif env_vars.get('MODE') == 'dev':
                            if overrides.get('mock') == True:
                                result['mocked'] = True
                            else:
                                if 't2_dev' not in result:
                                    result['t2_dev'] = []
                                result['t2_dev'].append(item.get('id'))
                    elif item.get('type') == 3:
                        if system_flags.get('legacy') == 1:
                            if user_context.get('dept') == 99:
                                for i in range(10):
                                    if item.get(f'prop_{i}'):
                                        if 'props' not in result:
                                            result['props'] = {}
                                        result['props'][f'p_{i}'] = item.get(f'prop_{i}')
                    else:
                        if env_vars.get('STRICT_TYPES') == 1:
                            return {"error": "invalid type"}
                        else:
                            result['unknown'] = item.get('val', 0)
                            
        elif type(data_payload) == dict:
            if data_payload.get('action') == 'update':
                if user_context.get('level') > 3:
                    if overrides.get('force') == True:
                        result['force_update'] = True
                        result['data'] = data_payload.get('data')
                    else:
                        if system_flags.get('readonly') != 1:
                            result['update'] = True
                            result['data'] = data_payload.get('data')
    return result
