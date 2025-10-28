import React, { useEffect, useRef } from 'react';

export const GraphBackground: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const lastFrameTimeRef = useRef<number>(0);
  const isVisibleRef = useRef(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Check for reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Visibility detection
    const handleVisibilityChange = () => {
      isVisibleRef.current = !document.hidden;
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Poisson-disk sampling for node distribution
    const nodes: Array<{ x: number; y: number; vx: number; vy: number; radius: number; color: string }> = [];
    const colors = ['#3AA6A0', '#4C5BD5', '#7C3AED', '#9AA3AF'];
    const minDist = 60;
    const maxDist = 120;

    // Create 150 nodes
    while (nodes.length < 150) {
      const x = Math.random() * canvas.width;
      const y = Math.random() * canvas.height;
      let valid = true;

      for (const node of nodes) {
        const dist = Math.sqrt(Math.pow(x - node.x, 2) + Math.pow(y - node.y, 2));
        if (dist < minDist) {
          valid = false;
          break;
        }
      }

      if (valid) {
        nodes.push({
          x,
          y,
          vx: (Math.random() - 0.5) * 0.2,
          vy: (Math.random() - 0.5) * 0.2,
          radius: 1.5 + Math.random() * 0.7,
          color: colors[Math.floor(Math.random() * colors.length)]
        });
      }
    }

    // Animation loop
    const animate = (currentTime: number) => {
      // Cap at ~60fps
      if (currentTime - lastFrameTimeRef.current < 16) {
        animationRef.current = requestAnimationFrame(animate);
        return;
      }

      if (!isVisibleRef.current) {
        animationRef.current = requestAnimationFrame(animate);
        return;
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      if (prefersReducedMotion) {
        // Static mode
        nodes.forEach((node) => {
          ctx.fillStyle = node.color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
          ctx.fill();
        });

        // Draw connections
        nodes.forEach((node, i) => {
          const neighbors: Array<{ node: typeof nodes[0], dist: number }> = [];
          nodes.forEach((other, j) => {
            if (i !== j) {
              const dist = Math.sqrt(Math.pow(node.x - other.x, 2) + Math.pow(node.y - other.y, 2));
              if (dist < maxDist) {
                neighbors.push({ node: other, dist });
              }
            }
          });
          neighbors.sort((a, b) => a.dist - b.dist);
          neighbors.slice(0, 2 + Math.floor(Math.random() * 2)).forEach(({ node: other, dist }) => {
            ctx.strokeStyle = node.color + Math.floor((1 - dist / maxDist) * 255 * 0.3).toString(16).padStart(2, '0');
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
          });
        });
      } else {
        // Animated mode with drift
        nodes.forEach((node) => {
          // Update position with random walk
          node.vx += (Math.random() - 0.5) * 0.02;
          node.vy += (Math.random() - 0.5) * 0.02;
          node.vx *= 0.99;
          node.vy *= 0.99;

          node.x += node.vx;
          node.y += node.vy;

          // Bounce with dampening
          if (node.x < 0 || node.x > canvas.width) {
            node.vx *= -0.8;
            node.x = Math.max(0, Math.min(canvas.width, node.x));
          }
          if (node.y < 0 || node.y > canvas.height) {
            node.vy *= -0.8;
            node.y = Math.max(0, Math.min(canvas.height, node.y));
          }

          // Draw node
          ctx.fillStyle = node.color;
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
          ctx.fill();
        });

        // Draw connections
        nodes.forEach((node, i) => {
          const neighbors: Array<{ node: typeof nodes[0], dist: number }> = [];
          nodes.forEach((other, j) => {
            if (i !== j) {
              const dist = Math.sqrt(Math.pow(node.x - other.x, 2) + Math.pow(node.y - other.y, 2));
              if (dist < maxDist) {
                neighbors.push({ node: other, dist });
              }
            }
          });
          neighbors.sort((a, b) => a.dist - b.dist);
          neighbors.slice(0, 2 + Math.floor(Math.random() * 2)).forEach(({ node: other, dist }) => {
            const opacity = (1 - dist / maxDist) * 0.3;
            ctx.strokeStyle = node.color + Math.floor(opacity * 255).toString(16).padStart(2, '0');
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
          });
        });
      }

      lastFrameTimeRef.current = currentTime;
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      aria-hidden="true"
    />
  );
};

