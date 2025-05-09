# Do & 8ly FAQ

## Team and Leadership

### Wouldn't the 8ly be stronger with a co-founding team?

You're absolutely right that diverse founding teams often bring complementary skills and perspectives. That's precisely why I'm actively seeking co-founders who share my vision of creating technology that feels innately human. As noted in the documentation, "Right now it's just me, Zech." I bring 20 years of coding experience and a Computer Science degree, but I recognize the value of adding co-founders with complementary expertise. Studies show that startups with complementary co-founding teams are more likely to succeed than solo ventures. While I'm building the foundation, I'm carefully seeking potential partners who align with my human-first philosophy rather than rushing this critical decision. The right co-founding team will help execute the vision more effectively and provide resilience through challenges.

### Do you have the AI/ML expertise required for this product?

While my background is in Computer Science with 20 years of coding experience, I recognize that specialized AI/ML expertise will be crucial for Do's success. That's exactly why finding co-founders or early team members with strong AI/ML backgrounds is a priority. Meanwhile, I've been deepening my knowledge in these areas. The initial prototype demonstrates my technical capability to begin implementation, but I'm transparent about needing to build a team with specialized expertise to fully realize my vision.

### How will you attract top technical talent in the competitive AI space?

Our advantage in attracting talent lies in our distinct vision. Unlike many AI companies focused on automation or efficiency, 8ly emphasizes "human-first technology" where AI works "silently in the background." This mission to create technology that "feels like a natural extension of thought" resonates with many top engineers tired of working on impersonal AI systems. Additionally, we plan to offer competitive compensation packages, emphasize work-life balance aligned with our philosophy, and provide meaningful ownership through equity. Our prototype already demonstrates technical feasibility, which helps attract those who want to work on products with clear potential.


### What happens if you burn out or face personal issues? Is there a succession plan?

This concern highlights exactly why building a strong co-founding team is my immediate priority. A well-structured founding team provides redundancy in leadership and reduces single-person risk. I'm documenting my vision, technical approach, and business strategy to ensure continuity. As we grow, we'll formalize succession planning and crisis management protocols. My personal experiences in management have taught me the importance of sustainable work practices and building resilient organizations that don't depend entirely on a single individual. This balanced approach to leadership is part of our "intentional living" philosophy.

### How will you balance technical development with business responsibilities?

This challenge is precisely why I'm prioritizing building a complementary founding team. In the short term, I'm taking a phased approach—focusing first on developing a compelling prototype that demonstrates our vision while simultaneously networking to find the right co-founders. As Liz Zalman points out in ["Founder vs Investor,"](https://startupnation.com/books/12-absolutes-of-fundraising-from-the-honest-truth-about-venture-capital-from-startup-to-ip/) co-founders who tag-team investor calls are significantly more effective at fundraising than solo founders. I've already created structured documentation of our vision, roadmap, and strategy to ensure clarity as we grow the team.

### Why should I believe you can execute on such an ambitious vision?

My 20 years of coding experience and Computer Science degree have equipped me with the technical foundation needed to begin implementing Do. What sets this apart from just another ambitious idea is that the vision emerged from solving real problems I've experienced personally with existing productivity tools. The prototype already demonstrates feasibility, showing that I can translate vision into execution. I recognize the scale of this challenge—that's why I'm seeking complementary co-founders and building relationships with advisors who have successfully scaled similar products. As Mike Mahlkow [notes in Forbes](https://www.forbes.com/councils/forbestechcouncil/2025/03/14/what-founders-get-wrong-about-fundraising-and-how-to-fix-it/), investors don't fund ideas; they fund execution. My track record of completing complex projects, combined with our clear roadmap and phased approach, demonstrates our commitment to disciplined execution.

### Do you have any industry experts or advisors supporting this venture?

We're actively building our advisory network, focusing on individuals with expertise in AI/ML, UX design, productivity tools, and startup scaling. Our approach to advisors is quality over quantity—seeking meaningful engagements with experts who genuinely believe in our vision rather than collecting impressive names. As we formalize these relationships, they'll become powerful advocates when approaching investors.

## Market and Business Model

### The productivity tool market is saturated. Why will users switch to Do?

You're right that the productivity market has many players, but it remains fundamentally broken for most users. Current tools force users to "manually prioritize, schedule, and track tasks," "juggle multiple apps for simple actions," and "sacrifice creativity and focus to rigid, robotic systems" as we note in our documentation. Do isn't just another task app—it represents a paradigm shift in how people interact with their tasks by eliminating the friction between thought and action. Our differentiator is making technology that feels "innately human" rather than adding to cognitive load. User research shows significant frustration with existing tools that require substantial manual management. By embedding action tools directly within tasks and enabling natural language input, we're addressing a persistent pain point that established players have failed to solve. The productivity market's size actually validates the opportunity—it's large enough that capturing even a small segment represents significant growth potential.

## Deployment and Infrastructure (Prototype)

### How is the Do prototype deployed?

The prototype is deployed to a Kubernetes cluster managed by DigitalOcean (DOKS). The deployment includes Kubernetes manifests for the application deployment, service, ingress (for URL routing and SSL), persistent volume claim (for the database), and secrets.

### How is website traffic routed to the prototype (e.g., `do.8ly.xyz`)?

An Ingress resource in Kubernetes, managed by Traefik (as an Ingress controller), routes external traffic from `do.8ly.xyz` to the appropriate service and pod running the Do application.

### How is SSL/TLS (HTTPS) handled for `do.8ly.xyz`?

SSL/TLS is handled by `cert-manager`, a Kubernetes add-on that automatically provisions and renews SSL certificates from issuers like Let's Encrypt. The Ingress resource is annotated to use `cert-manager`.

## Application Functionality & Features (Prototype)

### Q: Can the AI agent in the prototype access local files?

Yes, the AI agent (specifically the `LearnMoreAgent`) is designed to access certain files within the project directory (e.g., `README.md`, files in `docs/`, and parts of the source code itself) to answer questions accurately. This access is read-only and confined to the files packaged within the Docker container.

### What kind of AI models are being used or considered for the Do prototype's agents?

The prototype uses Google's Gemini 2.5 Pro and Gemini 2.5 Flash. It was originally using Llama 4's Maverick model on Grok, it struggled with tool use. Gemini 2.5 Pro is expensive but it gives the best performance we've seen yet. For the final iteration of Do, we intend to experiment with various models and features to keep inference costs as low as possible.

## Future and Vision

### Are there plans to support multiple users with isolated data in the final product?

Yes, the production application is going to have multi-tenancy and data isolation between users. This is a core architectural consideration for the production version, moving beyond the prototype's current single-database approach.

### How does 8ly plan to ensure user data privacy and security in the full product?

Data privacy and security are paramount. This involves industry best practices such as encryption at rest and in transit, robust authentication and authorization mechanisms, regular security audits, and compliance with relevant data protection regulations (e.g., GDPR, CCPA).

### What are the next immediate steps after this prototype phase?

We're currently seeking feedback from people we trust. We're also actively planning everything including architecture, design, feature set, user experience, and marketing. We hope to soon have a minimum viable product that could begin supporting early adopters and show the full potential of Do.

### How does 8ly envision "AI working silently in the background"?

This refers to AI that assists users without being intrusive or requiring constant explicit interaction. Instead of users managing complex AI prompts or settings, the AI in Do aims to understand context, anticipate needs, and automate or simplify tasks in a way that feels like a natural extension of the user's workflow, reducing cognitive load.