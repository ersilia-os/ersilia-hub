INSERT INTO WorkRequestData (
    RequestId,
    RequestPayload,
    RequestDate
)
SELECT Id, RequestPayload, RequestDate
FROM WorkRequest;
