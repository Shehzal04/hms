from datetime import date
from app.models.base import db
from app.models.hostel import Room, Bed, RoomAllocation, RoomTransferHistory
from app.models.student import Student

class AllocationError(Exception):
    """Custom exception for allocation logic violations."""
    pass

def allocate_bed_to_student(student_id, room_id, bed_id, check_in_date=None, expected_check_out_date=None, remarks=None):
    """
    Allocate a specific bed in a room to a student.
    Guarantees:
    - Student does not already have an active allocation.
    - Bed is currently available.
    - Updates bed status to 'Occupied'.
    - Updates room status.
    """
    student = Student.query.get(student_id)
    if not student:
        raise AllocationError("Student does not exist.")

    # Check existing active allocation
    active_alloc = RoomAllocation.query.filter_by(student_id=student_id, status='Active').first()
    if active_alloc:
        raise AllocationError(f"Student {student.full_name} is already allocated to Room {active_alloc.room.room_number}, Bed {active_alloc.bed.bed_number}.")

    room = Room.query.get(room_id)
    if not room:
        raise AllocationError("Selected room does not exist.")

    bed = Bed.query.get(bed_id)
    if not bed:
        raise AllocationError("Selected bed does not exist.")

    if bed.room_id != room.id:
        raise AllocationError("The selected bed does not belong to the selected room.")

    if bed.status != 'Available':
        raise AllocationError(f"Bed {bed.bed_number} is currently {bed.status} and cannot be allocated.")

    # Create allocation
    allocation = RoomAllocation(
        student_id=student.id,
        room_id=room.id,
        bed_id=bed.id,
        allocation_date=date.today(),
        check_in_date=check_in_date or date.today(),
        expected_check_out_date=expected_check_out_date,
        status='Active',
        remarks=remarks
    )
    bed.status = 'Occupied'
    room.sync_status()

    db.session.add(allocation)
    db.session.commit()
    return allocation


def transfer_student_bed(student_id, new_room_id, new_bed_id, reason, approved_by):
    """
    Transfers a student from their current active room/bed to a new room/bed.
    Records history in RoomTransferHistory.
    """
    active_alloc = RoomAllocation.query.filter_by(student_id=student_id, status='Active').first()
    if not active_alloc:
        raise AllocationError("Student does not have an active room allocation to transfer.")

    new_room = Room.query.get(new_room_id)
    new_bed = Bed.query.get(new_bed_id)

    if not new_room or not new_bed:
        raise AllocationError("Destination room or bed not found.")

    if new_bed.room_id != new_room.id:
        raise AllocationError("Destination bed does not belong to the selected room.")

    if new_bed.status != 'Available':
        raise AllocationError(f"Target bed {new_bed.bed_number} is not available (Status: {new_bed.status}).")

    old_room_id = active_alloc.room_id
    old_bed_id = active_alloc.bed_id
    old_bed = Bed.query.get(old_bed_id)
    old_room = Room.query.get(old_room_id)

    # Free old bed
    if old_bed:
        old_bed.status = 'Available'
    if old_room:
        old_room.sync_status()

    # Mark old allocation as Transferred
    active_alloc.status = 'Transferred'
    active_alloc.actual_check_out_date = date.today()

    # Record transfer history
    transfer_record = RoomTransferHistory(
        student_id=student_id,
        from_room_id=old_room_id,
        from_bed_id=old_bed_id,
        to_room_id=new_room.id,
        to_bed_id=new_bed.id,
        transfer_date=date.today(),
        reason=reason,
        approved_by=approved_by
    )
    db.session.add(transfer_record)

    # Create new active allocation
    new_alloc = RoomAllocation(
        student_id=student_id,
        room_id=new_room.id,
        bed_id=new_bed.id,
        allocation_date=date.today(),
        check_in_date=date.today(),
        status='Active',
        remarks=f"Transferred from Room {old_room.room_number if old_room else ''}. Reason: {reason}"
    )
    new_bed.status = 'Occupied'
    new_room.sync_status()

    db.session.add(new_alloc)
    db.session.commit()
    return new_alloc


def checkout_student_allocation(allocation_id, check_out_date=None, remarks=None):
    """
    Checks out a student, releases the bed, and updates the room status.
    """
    alloc = RoomAllocation.query.get(allocation_id)
    if not alloc:
        raise AllocationError("Allocation record not found.")

    if alloc.status != 'Active':
        raise AllocationError("This allocation is already inactive.")

    alloc.status = 'Checked Out'
    alloc.actual_check_out_date = check_out_date or date.today()
    if remarks:
        alloc.remarks = (alloc.remarks or '') + f" | Checkout Note: {remarks}"

    bed = alloc.bed
    if bed:
        bed.status = 'Available'
    room = alloc.room
    if room:
        room.sync_status()

    db.session.commit()
    return alloc
