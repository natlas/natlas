from app import db, mail
from app.models import User, UserInvitation


def test_new_anonymous_invite(app):  # type: ignore[no-untyped-def]
    test_invite = UserInvitation.new_invite()
    assert test_invite.token in UserInvitation.deliver_invite(test_invite)
    assert not test_invite.is_expired
    assert not test_invite.is_admin
    assert UserInvitation.get_invite(test_invite.token)
    test_invite.accept_invite()
    assert test_invite.accepted_date
    assert test_invite.is_expired
    db.session.rollback()


def test_new_email_invite(app):  # type: ignore[no-untyped-def]
    email = "test_invite@example.com"
    test_invite = UserInvitation.new_invite(email)
    with mail.record_messages() as outbox:
        UserInvitation.deliver_invite(test_invite)
    assert test_invite.email in outbox[0].recipients
    assert test_invite.token in outbox[0].body  # type: ignore[operator]
    assert UserInvitation.get_invite(test_invite.token)
    test_invite.accept_invite()
    assert test_invite.accepted_date
    assert test_invite.is_expired
    db.session.rollback()


def test_double_anonymous_deliver(app):  # type: ignore[no-untyped-def]
    test_invite = UserInvitation.new_invite()
    assert test_invite.token in UserInvitation.deliver_invite(test_invite)
    assert test_invite.token in UserInvitation.deliver_invite(test_invite)
    db.session.rollback()


def test_double_email_deliver(app):  # type: ignore[no-untyped-def]
    email = "test_invite@example.com"
    test_invite = UserInvitation.new_invite(email)
    with mail.record_messages() as outbox:
        UserInvitation.deliver_invite(test_invite)
        UserInvitation.deliver_invite(test_invite)
    assert len(outbox) == 2
    db.session.rollback()


def test_double_invite(app):  # type: ignore[no-untyped-def]
    email = "test_invite@example.com"
    invite_1 = UserInvitation.new_invite(email)
    old_token = invite_1.token
    # invite_2 should be an instance of UserInvitation(id=1) with a new token
    invite_2 = UserInvitation.new_invite(email)
    assert old_token != invite_2.token
    assert invite_1.token == invite_2.token
    assert not UserInvitation.get_invite(old_token)
    assert UserInvitation.get_invite(invite_1.token)
    db.session.rollback()


def test_inviting_existing_user(app):  # type: ignore[no-untyped-def]
    email = "test_invite@example.com"
    u = User(email=email)
    db.session.add(u)
    assert not UserInvitation.new_invite(email)
    db.session.rollback()
