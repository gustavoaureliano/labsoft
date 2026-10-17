from uuid import UUID, uuid4

import pytest

from app.media.models import Media


@pytest.fixture
def uploaded_video(upload_context):
    client, sessions, root = upload_context
    content = b"0123456789abcdefghijklmnop"
    response = client.post(
        "/api/media", files={"file": ("aula.mp4", content, "video/mp4")}
    )
    assert response.status_code == 201
    return client, sessions, root, response.json(), content


def test_get_metadata(uploaded_video):
    client, _, _, metadata, _ = uploaded_video
    response = client.get(f"/api/media/{metadata['id']}")
    assert response.status_code == 200
    assert response.json() == metadata
    assert "storage_key" not in response.json()


def test_get_full_video(uploaded_video):
    client, _, _, metadata, content = uploaded_video
    response = client.get(f"/api/media/{metadata['id']}/content")
    assert response.status_code == 200
    assert response.content == content
    assert response.headers["content-type"] == "video/mp4"
    assert int(response.headers["content-length"]) == len(content)
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-disposition"].startswith("inline;")
    assert response.headers["cache-control"] == "private, no-store"


@pytest.mark.parametrize(
    "interval,start,end", [("bytes=0-3", 0, 3), ("bytes=10-", 10, 25), ("bytes=-4", 22, 25)]
)
def test_video_ranges(uploaded_video, interval, start, end):
    client, _, _, metadata, content = uploaded_video
    response = client.get(
        f"/api/media/{metadata['id']}/content", headers={"Range": interval}
    )
    assert response.status_code == 206
    assert response.content == content[start:end + 1]
    assert response.headers["content-range"] == f"bytes {start}-{end}/{len(content)}"
    assert int(response.headers["content-length"]) == end - start + 1


def test_out_of_bounds_range(uploaded_video):
    client, _, _, metadata, content = uploaded_video
    response = client.get(
        f"/api/media/{metadata['id']}/content", headers={"Range": "bytes=999-"}
    )
    assert response.status_code == 416
    assert response.headers["content-range"] == f"bytes */{len(content)}"


@pytest.mark.parametrize("suffix", ["", "/content"])
def test_unknown_media(upload_context, suffix):
    client, _, _ = upload_context
    assert client.get(f"/api/media/{uuid4()}{suffix}").status_code == 404


def test_missing_file_keeps_metadata_accessible(uploaded_video):
    client, sessions, root, metadata, _ = uploaded_video
    with sessions() as session:
        media = session.get(Media, UUID(metadata["id"]))
        (root / media.storage_key).unlink()
    assert client.get(f"/api/media/{metadata['id']}/content").status_code == 404
    assert client.get(f"/api/media/{metadata['id']}").status_code == 200


@pytest.mark.parametrize("state", ["pending", "failed"])
def test_unavailable_media(uploaded_video, state):
    client, sessions, _, metadata, _ = uploaded_video
    with sessions() as session:
        media = session.get(Media, UUID(metadata["id"]))
        media.status = state
        session.commit()
    assert client.get(f"/api/media/{metadata['id']}/content").status_code == 404


def test_file_outside_storage_is_not_served(uploaded_video):
    client, sessions, root, metadata, _ = uploaded_video
    outside = root.parent / "outside.mp4"
    outside.write_bytes(b"outside storage")
    with sessions() as session:
        media = session.get(Media, UUID(metadata["id"]))
        media.storage_key = "../outside.mp4"
        session.commit()
    assert client.get(f"/api/media/{metadata['id']}/content").status_code == 404
