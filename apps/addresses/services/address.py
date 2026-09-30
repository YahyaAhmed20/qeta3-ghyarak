from django.db import transaction

from apps.addresses.models import Address


class AddressService:

    @staticmethod
    @transaction.atomic
    def create(
        *,
        customer,
        label,
        recipient_name,
        phone,
        city,
        area,
        address_line,
        building="",
        floor="",
        apartment="",
        landmark="",
        latitude=None,
        longitude=None,
        is_default=False,
    ):
        has_addresses = Address.objects.filter(
            customer=customer,
        ).exists()

        if not has_addresses:
            is_default = True

        if is_default:
            Address.objects.filter(
                customer=customer,
                is_default=True,
            ).update(is_default=False)

        return Address.objects.create(
            customer=customer,
            label=label,
            recipient_name=recipient_name,
            phone=phone,
            city=city,
            area=area,
            address_line=address_line,
            building=building,
            floor=floor,
            apartment=apartment,
            landmark=landmark,
            latitude=latitude,
            longitude=longitude,
            is_default=is_default,
        )

    @staticmethod
    @transaction.atomic
    def update(
        *,
        address,
        label=None,
        recipient_name=None,
        phone=None,
        city=None,
        area=None,
        address_line=None,
        building=None,
        floor=None,
        apartment=None,
        landmark=None,
        latitude=None,
        longitude=None,
        is_default=None,
    ):
        if label is not None:
            address.label = label.strip()

        if recipient_name is not None:
            address.recipient_name = recipient_name.strip()

        if phone is not None:
            address.phone = phone.strip()

        if city is not None:
            address.city = city.strip()

        if area is not None:
            address.area = area.strip()

        if address_line is not None:
            address.address_line = address_line.strip()

        if building is not None:
            address.building = building.strip()

        if floor is not None:
            address.floor = floor.strip()

        if apartment is not None:
            address.apartment = apartment.strip()

        if landmark is not None:
            address.landmark = landmark.strip()

        if latitude is not None:
            address.latitude = latitude

        if longitude is not None:
            address.longitude = longitude

        if is_default is True:
            Address.objects.filter(
                customer=address.customer,
                is_default=True,
            ).exclude(
                pk=address.pk,
            ).update(
                is_default=False,
            )

            address.is_default = True

        elif is_default is False and address.is_default:
            raise ValueError(
                "The default address cannot be unset. "
                "Set another address as default instead."
            )

        address.full_clean()
        address.save()

        return address

    @staticmethod
    @transaction.atomic
    def delete(*, address):
        was_default = address.is_default
        customer = address.customer

        address.delete()

        if was_default:
            replacement = (
                Address.objects
                .filter(customer=customer)
                .order_by("-created_at")
                .first()
            )

            if replacement:
                replacement.is_default = True
                replacement.save(
                    update_fields=[
                        "is_default",
                        "updated_at",
                    ],
                )