
import time
import datetime
from termcolor import colored
import mathphys
import pyaccel
import va


# def print_banner(prefix, li_pv_names=None,
#                          tb_pv_names=None,
#                          bo_pv_names=None,
#                          ts_pv_names=None,
#                          si_pv_names=None,
#                          ti_pv_names=None):
#
#     def c(msg,color=None,attrs=None):
#         if not attrs:
#             attrs=['bold']
#         return colored(msg,color=color,attrs=attrs)
#
#     print(r"")
#     print(c(r"         (___)    ",'white') + " | " + c("Virtual Accelerator with Channel Access server"))
#     print(c(r"    _____(.oo)    ",'white') + " | " + c("Version {0}".format(va.__version__)))
#     print(c(r"  //     ' ",'white')+c("@@     ",'magenta') + " | " + c("LNLS Accelerator Physics Group", attrs=['bold']))
#     print(c(r" # \ ,",'white')+c("VACA")+c(" /      ",'white') + " | " + c("Documentation: https://github.com/lnls-fac/va"))
#     print(c(" ~~~",'green') + c(r"\\",'white') + c("~~~",'green') + c(r"||",'white')+c("~~~~~  ",'green') + " | " + c("Prefix: {0}".format(prefix), attrs=['bold']))
#     print(c(r"    ^^   ^^       ",'white') + " | " + c("Number of SI pvs: {0}".format(len(si_pv_names))))
#     print(r"              "+c("\|/ ",'green') + " | " + c("Number of BO pvs: {0}".format(len(bo_pv_names))))
#     if li_pv_names is not None:
#         print(c(r"                  ",'white') + " | " + c("Number of LI pvs: {0}".format(len(li_pv_names))))
#     if ti_pv_names is not None:
#         print(c(r"                  ",'white') + " | " + c("Number of TI pvs: {0}".format(len(ti_pv_names))))
#     if tb_pv_names is not None:
#         print(c(r"                  ",'white') + " | " + c("Number of TB pvs: {0}".format(len(tb_pv_names))))
#     if ts_pv_names is not None:
#         print(c(r"                  ",'white') + " | " + c("Number of TS pvs: {0}".format(len(ts_pv_names))))
#     print(r"")


def log(message1='', message2='', c='white', a=None):
    t0 = time.time()
    st = datetime.datetime.fromtimestamp(t0).strftime('%Y-%m-%d %H:%M:%S')
    st = st + '.{0:03d}'.format(int(1000*(t0-int(t0))))
    if a is None: a = []
    strt = colored(st, 'white', attrs=[])
    str1 = colored('{0:<6.6s}'.format(message1), c, attrs=a)
    str2 = colored('{0}'.format(message2), c, attrs=a)
    strt = strt + ': ' + str1 + ' ' + str2
    print(strt)
    #return strt + ': ' + str1 + ' ' + str2


def process_and_wait_interval(processing_function, interval):
    start_time = time.time()
    processing_function()
    _wait_interval(start_time, interval)


def _wait_interval(start_time, interval):
    delta_t = time.time() - start_time
    if 0 < delta_t < interval:
        time.sleep(interval - delta_t)


# def charge_loss_fraction_line(accelerator, **kwargs):
#     """Calculate charge loss in a line
#
#     Keyword arguments:
#     twiss           -- Twiss parameters at the start of first element
#     global_coupling -- Global coupling
#     energy_spread   -- Relative energy spread
#     emittance       -- [m·rad]
#     delta_rx        -- [m]
#     delta_angle     -- [rad]
#     hmax            -- [m]
#     hmin            -- [m]
#     vmax            -- [m]
#     vmin            -- [m]
#
#     Returns loss fraction and twiss parameters in the last element of the accelerator
#     """
#
#     init_twiss, energy_spread, emittance, hmax, hmin, vmax, vmin = _process_loss_fraction_args(accelerator, **kwargs)
#     coupling = kwargs['global_coupling']
#
#     twiss, m66, transfer_matrices, orbit = pyaccel.optics.calc_twiss(accelerator, init_twiss = init_twiss)
#     betax, etax, betay, etay = pyaccel.optics.get_twiss(twiss, ('betax','etax','betay','etay'))
#     emitx = emittance * 1 / (1 + coupling)
#     emity = emittance * coupling / (1 + coupling)
#     sigmax = numpy.sqrt(betax * emitx + (etax * energy_spread)**2)
#     sigmay = numpy.sqrt(betay * emity + (etax * energy_spread)**2)
#     h_vc = hmax - hmin
#     v_vc = vmax - vmin
#     rx, ry = pyaccel.optics.get_twiss(twiss, ('rx','ry'))
#     xlim_inf, xlim_sup = rx - hmin, hmax - rx
#     ylim_inf, ylim_sup = ry - vmin, vmax - ry
#     xlim_inf[xlim_inf < 0] = 0
#     xlim_sup[xlim_sup < 0] = 0
#     ylim_inf[ylim_inf < 0] = 0
#     ylim_sup[ylim_sup < 0] = 0
#     xlim_inf[xlim_inf > h_vc] = 0
#     xlim_sup[xlim_sup > h_vc] = 0
#     ylim_inf[ylim_inf > v_vc] = 0
#     ylim_sup[ylim_sup > v_vc] = 0
#     min_xfrac_inf = numpy.amin(xlim_inf/sigmax)
#     min_xfrac_sup = numpy.amin(xlim_sup/sigmax)
#     min_yfrac_inf = numpy.amin(ylim_inf/sigmay)
#     min_yfrac_sup = numpy.amin(ylim_sup/sigmay)
#     sqrt2 = math.sqrt(2)
#
#     x_surviving_fraction = 0.5*math.erf(min_xfrac_inf/sqrt2) + \
#                            0.5*math.erf(min_xfrac_sup/sqrt2)
#     y_surviving_fraction = 0.5*math.erf(min_yfrac_inf/sqrt2) + \
#                            0.5*math.erf(min_yfrac_sup/sqrt2)
#     surviving_fraction = x_surviving_fraction * y_surviving_fraction
#     loss_fraction = 1.0 - surviving_fraction
#     return loss_fraction, twiss, m66, transfer_matrices, orbit
#
# def charge_loss_fraction_ring(accelerator, **kwargs):
#     """Calculate charge loss in a ring
#
#     Keyword arguments:
#     twiss         -- Twiss parameters at the start of first element
#     energy_spread -- Relative energy spread
#     emittance     -- [m·rad]
#     delta_rx      -- [m]
#     delta_angle   -- [rad]
#     hmax          -- [m]
#     hmin          -- [m]
#     vmax          -- [m]
#     vmin          -- [m]
#
#     Returns loss fraction and twiss parameters in the last element of the accelerator
#     """
#
#     init_twiss, energy_spread, emittance, hmax, hmin, vmax, vmin = _process_loss_fraction_args(accelerator, **kwargs)
#
#     init_pos = init_twiss.fixed_point
#     twiss,*_ = pyaccel.optics.calc_twiss(accelerator, init_twiss = init_twiss)
#     betax , betay, etax, etay = pyaccel.optics.get_twiss(twiss, ('betax', 'betay', 'etax', 'etay'))
#     if math.isnan(betax[-1]):
#         loss_fraction = 1.0
#         return loss_fraction
#
#     de = numpy.linspace(-(3*energy_spread), (3*energy_spread), 21)
#     de_probability = numpy.zeros(len(de))
#     lost_fraction = numpy.zeros(len(de))
#     total_lost_fraction = 0
#
#     for i in range(len(de)):
#         de_probability[i] = math.exp(-(de[i]**2)/(2*(energy_spread**2)))/(math.sqrt(2*math.pi)*energy_spread)
#         pos = [p for p in init_pos]
#         pos[4] += de[i]
#         orbit, *_ = pyaccel.tracking.linepass(accelerator, pos, indices = 'open')
#
#         if math.isnan(orbit[0,-1]):
#             lost_fraction[i] = 1.0
#             total_lost_fraction += de_probability[i]*lost_fraction[i]
#             continue
#
#         rx, ry = orbit[[0,2],:]
#         xlim_inf, xlim_sup = rx - hmin, hmax - rx
#         ylim_inf, ylim_sup = ry - vmin, vmax - ry
#         xlim_inf[xlim_inf < 0] = 0
#         xlim_sup[xlim_sup < 0] = 0
#         ylim_inf[ylim_inf < 0] = 0
#         ylim_sup[ylim_sup < 0] = 0
#         emit_x_inf = (xlim_inf**2  - (etax*energy_spread)**2)/betax
#         emit_x_sup = (xlim_sup**2  - (etax*energy_spread)**2)/betax
#         emit_y_inf = (ylim_inf**2  - (etay*energy_spread)**2)/betay
#         emit_y_sup = (ylim_sup**2  - (etay*energy_spread)**2)/betay
#         emit_x_inf[emit_x_inf < 0] = 0.0
#         emit_x_sup[emit_x_sup < 0] = 0.0
#         emit_y_inf[emit_y_inf < 0] = 0.0
#         emit_y_sup[emit_y_sup < 0] = 0.0
#         min_emit_x = numpy.amin([emit_x_inf, emit_x_sup])
#         min_emit_y = numpy.amin([emit_y_inf, emit_y_sup])
#         min_emit = min_emit_x + min_emit_y if min_emit_x*min_emit_y !=0 else 0.0
#         lf = math.exp(- min_emit/emittance)
#         lost_fraction[i] = lf if lf <1 else 1.0
#         total_lost_fraction += de_probability[i]*lost_fraction[i]
#
#     total_lost_fraction = total_lost_fraction/numpy.sum(de_probability)
#     loss_fraction = total_lost_fraction if total_lost_fraction < 1.0 else 1.0
#     return loss_fraction
#
# def shift_record_names(accelerator, record_names_dict):
#     new_dict = {}
#     for key in record_names_dict.keys():
#         new_dict[key] = {}
#         for k in record_names_dict[key].keys():
#             new_dict[key][k]= record_names_dict[key][k]
#     length = len(accelerator)
#     start = pyaccel.lattice.find_indices(accelerator, 'fam_name', 'start')[0]
#     for value in new_dict.values():
#         for key in value.keys():
#             indices = value[key]
#             new_indices = _shift_indices(indices, length, start)
#             value[key] = new_indices
#     return new_dict
#
# def _process_loss_fraction_args(accelerator, **kwargs):
#     energy_spread = kwargs['energy_spread']
#     emittance     = kwargs['emittance']
#
#     init_twiss = kwargs['init_twiss'] if 'init_twiss' in kwargs else kwargs['twiss_at_entrance']
#     delta_rx = kwargs['delta_rx'] if 'delta_rx' in kwargs else 0.0
#     delta_angle = kwargs['delta_angle'] if 'delta_angle' in kwargs else 0.0
#
#     if isinstance(init_twiss, dict):
#         init_twiss = pyaccel.optics.Twiss.make_new(init_twiss)
#     init_twiss.fixed_point = _transform_to_local_coordinates(init_twiss.fixed_point, delta_rx, delta_angle)
#
#     lattice = accelerator._accelerator.lattice
#     if 'hmax' in kwargs and 'hmin' in kwargs:
#         hmax = kwargs['hmax']
#         hmin = kwargs['hmin']
#     else:
#         hmax, hmin = numpy.array([(lattice[i].hmax,lattice[i].hmin) for i in range(len(accelerator))]).transpose()
#     if 'vmax' in kwargs and 'vmin' in kwargs:
#         vmax = kwargs['vmax']
#         vmin = kwargs['vmin']
#     else:
#         vmax, vmin = numpy.array([(lattice[i].vmax,lattice[i].vmin) for i in range(len(accelerator))]).transpose()
#     return init_twiss, energy_spread, emittance, hmax, hmin, vmax, vmin
#
# def _transform_to_local_coordinates(old_pos, delta_rx, delta_angle, delta_dl=0.0):
#     C, S = math.cos(delta_angle), math.sin(delta_angle)
#     old_angle = math.atan(old_pos[1])
#     new_pos = [p for p in old_pos]
#     new_pos[0] =  C * old_pos[0] + S * old_pos[5] + delta_rx
#     new_pos[5] = -S * old_pos[0] + C * old_pos[5] + delta_dl
#     new_pos[1] = math.tan(delta_angle + old_angle)
#     return new_pos
#
# def _shift_indices(indices, length, start):
#     try:
#         new_indices = indices[:]
#         for i in range(len(new_indices)):
#             if isinstance(new_indices[i], int):
#                 new_indices[i] = (new_indices[i] + start)%(length)
#             else:
#                 new_indices[i] = _shift_indices(new_indices[i], length, start)
#         return new_indices
#     except:
#         new_indices = (indices+start)%(length)
#         return new_indices
