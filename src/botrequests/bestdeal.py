from typing import Dict, Optional

from .service import get_location, get_queryset_for_bestdeal, time_for_the_week_ahead, get_properties_list, \
    unpacking_hotels_bestdeal
from .users import User


def get_list_hotels_bestdeal(user: Optional['User']) -> Dict | bool | None:
    quantity_days = time_for_the_week_ahead(check_in_date=user.check_in_date, check_out_date=user.check_out_date)
    try:
        querystring = get_queryset_for_bestdeal(
            destination_id=get_location(city=user.city),
            check_in_date=user.check_in_date,
            check_out_date=user.check_out_date,
            price_range=user.price_range
        )
    except KeyError:
        return
    data = get_properties_list(querystring=querystring)
    if data is None:
        return
    return unpacking_hotels_bestdeal(
        data=data,
        show_photo=user.show_photo,
        quantity_hotels=user.quantity_hotels,
        quantity_photo=user.quantity_photo,
        quantity_days=quantity_days,
        distance=user.distance
    )