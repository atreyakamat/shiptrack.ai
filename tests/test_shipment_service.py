import pytest
from backend.services.shipment_service import ShipmentService
from backend.models import Shipment

def test_create_shipment_valid(db):
    s = ShipmentService.create_shipment({'tracking_number': 'EM111222333IN', 'carrier': 'india_post', 'description': 'Docs'})
    assert s.id is not None
    assert s.tracking_number == 'EM111222333IN'
    assert s.description == 'Docs'

def test_get_shipment(db, sample_shipment):
    s = ShipmentService.get_shipment(sample_shipment.id)
    assert s.tracking_number == sample_shipment.tracking_number

def test_get_all_shipments(db, sample_shipment):
    shipments = ShipmentService.get_all_shipments()
    assert len(shipments) == 1
    assert shipments[0].id == sample_shipment.id

def test_update_shipment(db, sample_shipment):
    updated = ShipmentService.update_shipment(sample_shipment.id, {'description': 'Updated Docs'})
    assert updated.description == 'Updated Docs'

def test_delete_shipment(db, sample_shipment):
    assert ShipmentService.delete_shipment(sample_shipment.id) == True
    assert ShipmentService.get_shipment(sample_shipment.id) is None

def test_archive_shipment(db, sample_shipment):
    assert sample_shipment.is_archived == False
    archived = ShipmentService.archive_shipment(sample_shipment.id)
    assert archived == True

def test_search_shipments(db, sample_shipment):
    results = ShipmentService.search_shipments('EM123')
    assert len(results) == 1
    results = ShipmentService.search_shipments('Nonexistent')
    assert len(results) == 0
