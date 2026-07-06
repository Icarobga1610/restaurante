const base64urlToBuffer = (value) => {
  const padding = '='.repeat((4 - (value.length % 4)) % 4);
  const base64 = (value + padding).replace(/-/g, '+').replace(/_/g, '/');
  const binary = window.atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
};

const bufferToBase64url = (buffer) => {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i += 1) binary += String.fromCharCode(bytes[i]);
  return window.btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
};

const prepareCreateOptions = (publicKey) => ({
  ...publicKey,
  challenge: base64urlToBuffer(publicKey.challenge),
  user: {
    ...publicKey.user,
    id: base64urlToBuffer(publicKey.user.id),
  },
  excludeCredentials: (publicKey.excludeCredentials || []).map((credential) => ({
    ...credential,
    id: base64urlToBuffer(credential.id),
  })),
});

const prepareGetOptions = (publicKey) => ({
  ...publicKey,
  challenge: base64urlToBuffer(publicKey.challenge),
  allowCredentials: (publicKey.allowCredentials || []).map((credential) => ({
    ...credential,
    id: base64urlToBuffer(credential.id),
  })),
});

export const browserSupportsWebAuthn = () => Boolean(window.PublicKeyCredential && navigator.credentials);

export async function createWebAuthnCredential(publicKey) {
  const credential = await navigator.credentials.create({ publicKey: prepareCreateOptions(publicKey) });
  return {
    credential_id: bufferToBase64url(credential.rawId),
    raw_id: bufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      attestationObject: bufferToBase64url(credential.response.attestationObject),
      clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
    },
  };
}

export async function getWebAuthnCredential(publicKey) {
  const credential = await navigator.credentials.get({ publicKey: prepareGetOptions(publicKey) });
  return {
    credential_id: bufferToBase64url(credential.rawId),
    type: credential.type,
    response: {
      authenticatorData: bufferToBase64url(credential.response.authenticatorData),
      clientDataJSON: bufferToBase64url(credential.response.clientDataJSON),
      signature: bufferToBase64url(credential.response.signature),
      userHandle: credential.response.userHandle ? bufferToBase64url(credential.response.userHandle) : null,
    },
  };
}
