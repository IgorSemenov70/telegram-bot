from typing import Dict, Optional, Any

from .service import get_location, get_queryset_for_lowerprice_and_highprice, time_for_the_week_ahead, \
    get_properties_list, unpacking_hotels_lowprice_and_highprice
from .users import User


def get_list_hotels(user: Optional['User']) -> Dict[str, Any] | bool | None:
    quantity_days = time_for_the_week_ahead(check_in_date=user.check_in_date, check_out_date=user.check_out_date)
    try:
        querystring = get_queryset_for_lowerprice_and_highprice(
            destination_id=get_location(city=user.city),
            check_in_date=user.check_in_date,
            check_out_date=user.check_out_date,
            sortorder=user.sortorder
        )
    except KeyError:
        return
    data = get_properties_list(querystring=querystring)
    if data is None:
        return
    return unpacking_hotels_lowprice_and_highprice(
        data=data,
        show_photo=user.show_photo,
        quantity_hotels=user.quantity_hotels,
        quantity_photo=user.quantity_photo,
        quantity_days=quantity_days
    )
