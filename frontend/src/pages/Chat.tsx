import ChatInterfaceV2 from '../components/ChatInterfaceV2';
import MainLayout from '../layouts/MainLayout';

export default function Chat() {
  return (
    <MainLayout activeModule="search">
      <ChatInterfaceV2 module="search" isMain={true} />
    </MainLayout>
  );
}

