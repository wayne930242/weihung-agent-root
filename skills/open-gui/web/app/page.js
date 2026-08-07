import { SocketProvider } from "../components/SocketProvider";
import { PreviewProvider } from "../components/PreviewProvider";
import FatalBanner from "../components/FatalBanner";
import SessionEndedBanner from "../components/SessionEndedBanner";
import SplitView from "../components/SplitView";
import PreviewPanel from "../components/PreviewPanel";

export default function Page() {
  return (
    <SocketProvider>
      <PreviewProvider>
        <FatalBanner />
        <SessionEndedBanner />
        <SplitView />
        <PreviewPanel />
      </PreviewProvider>
    </SocketProvider>
  );
}
