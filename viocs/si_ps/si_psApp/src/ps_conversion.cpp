/*
 * Conversion of power supply values using excitation tables.
 */

#include <dbDefs.h>
#include <registryFunction.h>
#include <subRecord.h>
#include <aSubRecord.h>
#include <epicsExport.h>

#include "unit_converter.h"


int num_conversions;
UnitConverter* converter;


long ps_conversion_init(struct subRecord *psub)
{
    num_conversions = psub->a;
    converter = new UnitConverter(psub->name);
    return 0;
}

long ps_conversion_phys2eng_process(struct subRecord *psub)
{
    switch (num_conversions) {
        case 2:
            psub->e = converter->convert_phys2eng(psub->d);
        case 1:
            psub->c = converter->convert_phys2eng(psub->b);
    }

    return 0;
}

long ps_conversion_eng2phys_process(struct subRecord *psub)
{
    switch (num_conversions) {
        case 2:
            psub->e = converter->convert_eng2phys(psub->d);
        case 1:
            psub->c = converter->convert_eng2phys(psub->b);
    }

    return 0;
}


epicsRegisterFunction(ps_conversion_init);
epicsRegisterFunction(ps_conversion_phys2eng_process);
epicsRegisterFunction(ps_conversion_eng2phys_process);
